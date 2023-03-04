import sys
import json
from dataclasses import asdict

from komandr import command, arg, main as komandr_main

from seal.config import Config
from seal.ast import Node, NodeError
from seal import langspec


@command
@arg('file', help='file to read')
@arg('pragma_version', '-p', help="pragma version", type=int)
def compile(path, pragma_version=8):
    with open(path, encoding='utf-8') as f:
        config = Config(pragma_version=pragma_version)
        try:
            print(Node.from_file(f, config=config))
        except NodeError as e:
            print('Compiler error: {}'.format(str(e)), file=sys.stderr)
            if e.token:
                print('Ln: {}, Col: {}, Token: {}'.format(
                    e.token.line, e.token.col, e.token.value
                ), file=sys.stderr)
            exit(1)


@command
def spec(opcode: str):
    try:
        print(json.dumps(asdict(langspec.opcodes[opcode]), indent=4))
    except KeyError:
        print('Opcode not found', file=sys.stderr)
        exit(1)


def main(*args, **kwargs):
    komandr_main(*args, **kwargs)
