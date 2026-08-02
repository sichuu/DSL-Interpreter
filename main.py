"""Entry point: run a .dsl script, or start an interactive REPL."""
import sys

from lexer import Lexer, LexerError
from dsl_parser import Parser, ParserError
from interpreter import Interpreter, DSLRuntimeError


def run_source(source: str, interpreter: Interpreter) -> bool:
    try:
        tokens = Lexer(source).tokenize()
        statements = Parser(tokens).parse()
        interpreter.run(statements)
        return True
    except (LexerError, ParserError, DSLRuntimeError) as e:
        print(f"Error: {e}")
        return False


def run_file(path: str):
    with open(path, 'r') as f:
        source = f.read()
    run_source(source, Interpreter())


def repl():
    print("Data Analysis DSL — type EXIT to quit")
    interpreter = Interpreter()
    while True:
        try:
            line = input("dsl> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip().upper() == 'EXIT':
            break
        if line.strip():
            run_source(line, interpreter)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()
