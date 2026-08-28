import sys
from lexer import Lexer, LangSyntaxError
from parser import Parser
from interpreter import Interpreter, LangRuntimeError
from repl import Repl


def run_source(source):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse_program()
    Interpreter().run(program)


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            source = f.read()
        try:
            run_source(source)
        except (LangSyntaxError, LangRuntimeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        Repl().run()
        print("Error: no input files")

if __name__ == '__main__':
    main()
