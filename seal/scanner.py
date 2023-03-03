import sys
from enum import Enum
from typing import TextIO, Generator, List, Tuple, TypeVar, Generic, Optional
from collections.abc import Callable
from dataclasses import dataclass

STRING_DELIMETER = '"'
COMMENT_DELIMETER = '\''
LABEL_SUFFIX = ':'
LEFT_PAREN = '('
RIGHT_PAREN = ')'
VAR_PREFIX = '$'
CONST_PREFIX = '@'
NEWLINE = '\n'
IN = '#in'
CASE = '#case'
WHILE = '#while'
FN = '#fn'


TERMINALS = [LEFT_PAREN, RIGHT_PAREN, STRING_DELIMETER, NEWLINE]

TokenType = Enum('TokenType', [
    'BEGIN',
    'END',
    'BYTE',
    'INT',
    'OPCODE',
    'LABEL',
    'VARIABLE',
    'COMMENT',
    'IN',
    'CASE',
    'WHILE',
    'FN',
    'ROOT',
    'CONSTANT'
])


T = TypeVar('T')


@dataclass
class Token(Generic[T]):
    DELIMETER = '.'

    token_type: TokenType
    value: str
    line: Optional[int] = 0
    loc: Optional[int] = 0
    col: Optional[int] = 0

    @classmethod
    def root(cls) -> T:
        return Token(token_type=TokenType.ROOT, value='', line=0, loc=0,
                     col=0)

    @property
    def fragments(self) -> List[str]:
        return self.value.split(self.DELIMETER)

    @property
    def head(self) -> str:
        return self.fragments[0]

    @property
    def rest(self) -> List[str]:
        return self.fragments[1:] if len(self.fragments) > 0 else []

    def __repr__(self) -> str:
        return '{}({})'.format(self.token_type.name, self.value)


def scan(f: TextIO) -> Generator[Token, None, None]:

    line = 1
    col = 1
    loc = 0

    def consume_one() -> str:
        nonlocal line, loc, col
        c = f.read(1)
        if c == NEWLINE:
            line += 1
            col = 1
        else:
            col += 1
        loc += 1
        return c

    def consume(unless: Callable, c: str) -> Tuple[str, str]:
        value = ''
        while unless(c):
            value += c
            c = consume_one()
        return c, value

    def atom_test(c) -> bool:
        return c not in TERMINALS and not c.isspace()

    def token(*args, **kwargs):
        kwargs['line'] = line
        kwargs['loc'] = loc
        kwargs['col'] = col
        return Token(*args, **kwargs)

    c = consume_one()
    while c:
        if c == LEFT_PAREN:
            yield token(TokenType.BEGIN, LEFT_PAREN)
            c = consume_one()
        elif c == RIGHT_PAREN:
            yield token(TokenType.END, RIGHT_PAREN)
            c = consume_one()
        elif c == COMMENT_DELIMETER:
            c, value = consume(lambda c: c != COMMENT_DELIMETER, consume_one())
            yield token(TokenType.COMMENT, value)
            c = consume_one()
        elif c == STRING_DELIMETER:
            c, value = consume(lambda c: c != STRING_DELIMETER, consume_one())
            yield token(TokenType.BYTE, '"{}"'.format(value))
            c = consume_one()
        elif c.isnumeric():
            c, value = consume(lambda c: c.isnumeric(), c)
            yield token(TokenType.INT, value)
        elif atom_test(c):
            c, value = consume(atom_test, c)
            if value.endswith(LABEL_SUFFIX):
                yield token(TokenType.LABEL, value)
            elif value.startswith(VAR_PREFIX):
                yield token(TokenType.VARIABLE, value)
            elif value.startswith(CONST_PREFIX):
                yield token(TokenType.CONSTANT, value)
            elif value == IN:
                yield token(TokenType.IN, value)
            elif value == CASE:
                yield token(TokenType.CASE, value)
            elif value == WHILE:
                yield token(TokenType.WHILE, value)
            elif value == FN:
                yield token(TokenType.FN, value)
            else:
                yield token(TokenType.OPCODE, value)
        else:
            c = consume_one()


def main():
    with open(sys.argv[1]) as f:
        for token in scan(f):
            print(token)


if __name__ == '__main__':
    main()
