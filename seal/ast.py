from io import IOBase, StringIO
from typing import TypeVar, Generic, List, Generator, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict
from seal import langspec
from seal.config import Config
from seal.scanner import TokenType, Token, scan

max_scratch_space = 256
scratch_space: List[str] = []
label_counter = defaultdict(lambda: 0)
constants: Dict[str, str or int] = {}


def allocate_label(label: str = None) -> int:
    label = label or 'label'
    counter = label_counter[label]
    alias = f'{label}_{counter}'
    label_counter[label] += 1
    return alias


def allocate_scratch_space(name: str) -> int:
    index = refer_scratch_space(name)
    if index >= 0:
        return index
    index = len(scratch_space)
    if index < max_scratch_space:
        scratch_space.append(name)
        return index
    return -1


def refer_scratch_space(name) -> int:
    try:
        return scratch_space.index(name)
    except ValueError:
        return -1


class NodeError(Exception):

    def __init__(self, msg, token: Token = None):
        super().__init__(msg)
        self.token = token


T = TypeVar('T')


@dataclass
class Node(Generic[T]):

    token: Token
    children: Optional[List[T]] = None
    doc: Optional[str] = None
    config: Optional[Config] = None
    alias: Optional[str] = None

    @property
    def command(self) -> str:
        return self.alias or self.token.head

    @property
    def statement(self) -> str:
        return self.command

    def __post_init__(self):
        self.validate()

    def validate(self):
        pass

    def emit(self) -> List[str]:
        lines = []
        if self.children:
            for child in self.children:
                lines.extend(child.emit())
        if self.token:
            if self.doc:
                lines.append('{} // {}'.format(self.statement, self.doc))
            else:
                lines.append('{}'.format(self.statement))
        return lines

    def write(self, f: IOBase):
        f.writelines(['{}\n'.format(line) for line in self.emit() if line])

    def __str__(self) -> str:
        with StringIO() as io:
            self.write(io)
            return io.getvalue()

    @classmethod
    def from_str(cls, input, config: Optional[Config] = None, root: T = None,
                 children: List[T] = None):
        return Node.from_tokens(scan(StringIO(input)), config=config,
                                root=root, children=children)

    @classmethod
    def from_file(cls, file, config: Optional[Config] = None, root: T = None,
                  children: List[T] = None):
        return Node.from_tokens(scan(file), config=config, root=root,
                                children=children)

    @classmethod
    def from_tokens(cls, tokens: Generator[Token, None, None],
                    config: Config = None, root: T = None,
                    children: List[T] = None) -> T:
        config = config or Config()

        if not children:
            children = []
            while True:
                try:
                    children.append(
                        Node._from_tokens(tokens, config=config)
                    )
                except StopIteration:
                    break

        if not root:
            root = Root(Token.root(), children=children, config=config)
        return root

    @classmethod
    def _from_tokens(cls, tokens: Generator[Token, None, None],
                     head: Optional[Token] = None,
                     children: Optional[List[T]] = None,
                     config: Optional[Config] = None) -> T:
        token = head or next(tokens)
        if token.token_type == TokenType.BEGIN:
            head = next(tokens)
            token = next(tokens)
            children = []
            while token.token_type != TokenType.END:
                child = Node._from_tokens(tokens, head=token, config=config)
                children.append(child)
                token = next(tokens)
            if token.token_type != TokenType.END:
                raise NodeError('Unclosed expression', token=token)
            return Node._from_tokens(tokens,
                                     head=head,
                                     children=children,
                                     config=config)
        elif token.token_type == TokenType.OPCODE:
            return Opcode(token, children=children, config=config)
        elif token.token_type == TokenType.VARIABLE:
            return Variable(token, children=children, config=config)
        elif token.token_type == TokenType.CONSTANT:
            return Const(token, children=children, config=config)
        elif token.token_type == TokenType.BYTE:
            return Opcode(token,
                          alias='byte',
                          children=children,
                          immediate_args_override=[token.value],
                          config=config)
        elif token.token_type == TokenType.INT:
            return Opcode(token,
                          alias='int',
                          children=children,
                          immediate_args_override=[token.value],
                          config=config)
        elif token.token_type == TokenType.LABEL:
            return Label(token, children=children, config=config)
        elif token.token_type == TokenType.COMMENT:
            return Comment(token, children=children, config=config)
        elif token.token_type == TokenType.IN:
            return In(token, children=children, config=config)
        elif token.token_type == TokenType.CASE:
            return Case(token, children=children, config=config)
        elif token.token_type == TokenType.WHILE:
            return While(token, children=children, config=config)
        elif token.token_type == TokenType.FN:
            return Function(token, children=children, config=config)
        elif token.token_type == TokenType.ITXN:
            return ITxn(token, children=children, config=config)

        raise NodeError('Invalid token', token=token)


@dataclass
class Opcode(Node):

    NONSTRICT_FLAG = '\''

    spec: Optional[langspec.Opcode] = None
    immediate_args_override: Optional[List[str]] = None

    @property
    def immediate_args(self) -> List[str]:
        return self.immediate_args_override or self.token.rest

    @property
    def statement(self) -> str:
        return ' '.join([self.spec.name, *self.immediate_args])

    @property
    def children_height(self) -> int:
        total_height = 0
        for child in self.children or []:
            if isinstance(child, Const):
                if child.children:
                    child = child.children[0]
                else:
                    child = constants[child.command]

            if isinstance(child, Opcode) and child.spec.returns:
                total_height += len(child.spec.returns)
        return total_height

    @property
    def return_height(self) -> int:
        return len(self.spec.returns or [])

    @property
    def arg_height(self) -> int:
        return len(self.spec.args or [])

    @property
    def command(self) -> str:
        return self.alias or self.token.head.lstrip(self.NONSTRICT_FLAG)

    def validate(self):

        super().validate()

        try:
            self.spec = langspec.opcodes[self.command]
        except KeyError:
            raise NodeError('Invalid opcode', token=self.token)

        nonstrict = self.token.value.startswith(self.NONSTRICT_FLAG)

        if nonstrict:
            return

        if self.arg_height != self.children_height:
            raise NodeError('Invalid number of stack args', token=self.token)

        if self.spec.immediate_args:
            if len(self.immediate_args) != len(self.spec.immediate_args):
                raise NodeError('Invalid number of immediate args',
                                token=self.token)

            for i, arg in enumerate(self.immediate_args):
                spec = self.spec.immediate_args[i]
                if spec.reference:
                    enums = langspec.fields[self.command]
                    if arg not in enums:
                        raise NodeError(
                            'Invalid arg, need one of the following: {}'
                            .format(', '.join(enums)),
                            token=self.token
                        )
                else:
                    # Validate non-ref immediate args
                    pass


class Label(Node):

    def emit(self) -> List[str]:
        lines = []
        lines.append(self.command)
        for child in self.children:
            lines.extend(child.emit())
        return lines


class Comment(Node):

    def emit(self) -> List[str]:
        # Do not emit anything for comments
        return []


class In(Node):

    def validate(self):
        super().validate()
        if not self.children or len(self.children) < 2:
            raise NodeError('#in requires 2 childs at min')

        all_case = all([c.token.token_type == TokenType.CASE
                        for c in self.children])
        if not all_case:
            raise NodeError('#in requires all childs to be a #case')

    def emit(self) -> List[str]:
        label = allocate_label('in')
        lines = []
        for child in self.children:
            lines.extend(child.emit())
            lines.append(f'b {label}')
        lines.append(f'{label}:')
        return lines


class Case(Node):

    def validate(self):
        super().validate()
        if not self.children or len(self.children) < 2:
            raise NodeError('#case requires min two childs')

    def emit(self) -> List[str]:
        label = allocate_label('case')
        lines = []
        lines.extend(self.children[0].emit())
        lines.append(f'bz {label}')
        for child in self.children[1:]:
            lines.extend(child.emit())
        lines.append(f'{label}:')
        return lines


class While(Node):

    def validate(self):
        super().validate()
        if not self.children or len(self.children) < 2:
            raise NodeError('#while requires min two childs')

    def emit(self) -> List[str]:
        label = allocate_label('while')
        lines = []
        lines.append(f'{label}:')
        lines.extend(self.children[0].emit())
        lines.append(f'bz {label}_end')
        for child in self.children[1:]:
            lines.extend(child.emit())
        lines.append(f'b {label}')
        lines.append(f'{label}_end:')
        return lines


class Function(Node):
    pass


class Variable(Opcode):

    def validate(self):
        if self.children:
            index = allocate_scratch_space(self.command)
            if index < 0:
                raise NodeError('Scratch space overflow', token=self.token)
            self.immediate_args_override = [str(index)]
            self.doc = self.command
            self.alias = 'store'
        else:
            index = refer_scratch_space(self.command)
            if index < 0:
                raise NodeError('Scratch space not found', token=self.token)
            self.immediate_args_override = [str(index)]
            self.doc = self.command
            self.alias = 'load'
        super().validate()


class Const(Node):

    def validate(self):
        super().validate()
        if self.children:
            if len(self.children) != 1:
                raise NodeError('Constants requires only one single child')
            valid_childs = [TokenType.BYTE, TokenType.INT]
            if self.children[0].token.token_type not in valid_childs:
                raise NodeError(
                    f'Constants accepts only the following: {valid_childs}'
                )
            if self.token.value in constants:
                raise NodeError(
                    f'Constant already defined {self.token.value}'
                )

            constants[self.command] = self.children[0]
        else:
            if self.command not in constants:
                raise NodeError(f'Constant {self.command} not defined yet',
                                token=self.token)

    def emit(self) -> List[str]:
        if self.children:
            return []
        line = constants[self.command].emit().pop()
        return [f'{line} // {self.token.value}']


class Root(Node):

    def emit(self) -> List[str]:
        lines = ['#pragma version {}'.format(self.config.pragma_version)]
        lines.extend(super().emit())
        return lines


class ITxn(Node):

    def validate(self):
        super().validate()
        if not self.children or len(self.children) == 0:
            raise NodeError('#itxn requires 1 childs at min')

        all_field = all([c.command == 'itxn_field' for c in self.children])
        if not all_field:
            raise NodeError('#itxn requires all childs to be a itxn_field')

    def emit(self) -> List[str]:
        lines = []
        lines.append('itxn_begin')
        for child in self.children[1:]:
            lines.extend(child.emit())
        lines.append('itxn_submit')
        return lines
