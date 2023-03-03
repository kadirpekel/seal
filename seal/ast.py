from io import IOBase, StringIO
from typing import TypeVar, Generic, List, Generator, Optional, Dict
from dataclasses import dataclass

from seal import langspec
from seal.config import Config
from seal.scanner import TokenType, Token, scan

max_scratch_space = 256
scratch_space: List[str] = []
case_counter = 0
constants: Dict[str, str or int] = {}


def allocate_case_label() -> int:
    global case_counter
    alias = 'label_{}'.format(case_counter)
    case_counter += 1
    return alias


def allocate_scratch_space(name: str) -> int:
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


class CompilerError(Exception):

    def __init__(self, msg, token: Token = None):
        super().__init__(msg)
        self.token = token


T = TypeVar('T')


@dataclass
class Node(Generic[T]):

    token: Token
    children: Optional[List[T]] = None
    immediate_args_override: Optional[List[str]] = None
    doc: Optional[str] = None
    config: Optional[Config] = None
    alias: Optional[str] = None

    @property
    def noncomments(self) -> List[T]:
        if self.children:
            return list(
                filter(lambda c: c.token.token_type != TokenType.COMMENT,
                       self.children)
            )
        return []

    @property
    def command(self) -> str:
        return '{}'.format(self.alias) if self.alias else self.token.head

    @property
    def immediate_args(self) -> List[str]:
        return self.immediate_args_override or self.token.rest

    @property
    def statement(self) -> str:
        return ' '.join([self.command, *self.immediate_args])

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
                raise CompilerError('Unclosed expression', token=token)
            return Node._from_tokens(tokens,
                                     head=head,
                                     children=children,
                                     config=config)
        elif token.token_type == TokenType.OPCODE:
            try:
                return Opcode(token,
                              children=children,
                              spec=langspec.opcodes[token.head],
                              config=config)
            except KeyError:
                raise CompilerError('Invalid opcode', token=token)
        elif token.token_type == TokenType.VARIABLE:
            return Variable(token, children=children, config=config)
        elif token.token_type == TokenType.CONSTANT:
            return Const(token, children=children, config=config)
        elif token.token_type == TokenType.BYTE:
            return Opcode(token,
                          spec=langspec.opcodes['byte'],
                          children=children,
                          immediate_args_override=[token.value],
                          config=config)
        elif token.token_type == TokenType.INT:
            return Opcode(token,
                          spec=langspec.opcodes['int'],
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

        raise CompilerError('Invalid token', token=token)


@dataclass
class Opcode(Node):

    spec: langspec.Opcode = None

    @property
    def statement(self) -> str:
        return ' '.join([self.spec.name, *self.immediate_args])

    @property
    def children_height(self) -> int:
        return sum([len(c.spec.returns or []) for c in self.noncomments])

    @property
    def return_height(self) -> int:
        return len(self.spec.returns or [])

    @property
    def arg_height(self) -> int:
        return len(self.spec.args or [])

    def validate(self):

        super().validate()

        if self.spec.args:
            if self.config.strict and self.arg_height != self.children_height:
                raise CompilerError('Invalid number of stack args',
                                    token=self.token)

        if self.config.strict and self.spec.immediate_args:
            if len(self.immediate_args) != len(self.spec.immediate_args):
                raise CompilerError('Invalid number of immediate args',
                                    token=self.token)

            for i, arg in enumerate(self.immediate_args):
                spec = self.spec.immediate_args[i]
                if spec.reference:
                    enums = langspec.fields[self.command]
                    if arg not in enums:
                        raise CompilerError(
                            'Invalid arg, need one of the following: {}'
                            .format(', '.join(enums)),
                            token=self.token
                        )
                else:
                    # Validate non-ref immediate args
                    pass


class Label(Node):

    def emit(self) -> List[str]:
        lines = super().emit()
        lines.insert(0, lines.pop())
        return lines


class Comment(Node):

    def emit(self) -> List[str]:
        # Do not emit anything for comments
        return []


class In(Node):

    def validate(self):
        super().validate()
        all_case = all([c.token.token_type == TokenType.CASE
                        for c in self.noncomments])
        if not all_case:
            raise CompilerError('#in requires all childs to be a #case')

        label = allocate_case_label()
        self.alias = f'{label}:'
        for child in self.children:
            child.children[1] = Opcode(child.children[1].token,
                                       spec=langspec.opcodes['b'],
                                       immediate_args_override=[label],
                                       children=[child.children[1]],
                                       config=Config)


class Case(Node):

    def validate(self):
        super().validate()
        if len(self.noncomments) != 2:
            raise CompilerError('#case requires exactly two childs')

        label = allocate_case_label()
        self.alias = f'{label}:'
        self.noncomments[0] = Opcode(self.noncomments[0].token,
                                     spec=langspec.opcodes['bz'],
                                     immediate_args_override=[label],
                                     children=[self.noncomments[0]],
                                     config=self.config)


class While(Node):
    pass


class Function(Node):
    pass


class Variable(Opcode):

    def validate(self):
        if self.noncomments:
            index = allocate_scratch_space(self.token.value)
            if index < 0:
                raise CompilerError('Scratch space overflow', token=self.token)
            self.immediate_args_override = [str(index)]
            self.doc = self.token.value
            self.spec = langspec.opcodes['store']
        else:
            index = refer_scratch_space(self.token.value)
            if index < 0:
                raise CompilerError('Scratch space not found',
                                    token=self.token)
            self.immediate_args_override = [str(index)]
            self.doc = self.token.value
            self.spec = langspec.opcodes['load']
        super().validate()


class Const(Opcode):

    assigned: Optional[Opcode] = None

    def validate(self):
        if self.noncomments:
            if len(self.noncomments) != 1:
                raise CompilerError('constants requires only one single child')
            self.assigned = self.noncomments[0]
            valid_childs = [TokenType.BYTE, TokenType.INT]
            if self.assigned.token.token_type not in valid_childs:
                raise CompilerError(
                    f'constants accepts only the following: {valid_childs}'
                )
            if self.token.value in constants:
                raise CompilerError(
                    f'constant already defined {self.token.value}'
                )

            constants[self.token.value] = self.assigned
        else:
            try:
                self.assigned = constants[self.command]
            except KeyError:
                raise CompilerError('Constant not defined yet',
                                    token=self.token)

        self.spec = self.assigned.spec
        super().validate()

    def emit(self) -> List[str]:
        if self.noncomments:
            return []
        return self.assigned.emit()


class Root(Node):

    def emit(self) -> List[str]:
        lines = super().emit()
        lines.insert(0,
                     '#pragma version {}'.format(self.config.pragma_version))
        return lines
