import sys
from interpreter import Interpreter, LangRuntimeError
from lexer import Lexer, LangSyntaxError
from parser import Parser


class Repl:
    def __init__(self):
        self.interpreter = Interpreter()
        self.source_buffer = ""

    def run(self):
        print("lang repl (ctrl+d to exit)")
        while True:
            try:
                prompt = ".. " if self.source_buffer else ">> "
                line = input(prompt)
                if not line.strip() and not self.source_buffer:
                    continue
                self.source_buffer += line + "\n"
                if not self._execute_buffer():
                    self.source_buffer = ""

            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")
                self.source_buffer = ""
            except EOFError:
                print()
                break

    def _execute_buffer(self):
        # returns true if multiline
        try:
            tokens = Lexer(self.source_buffer).tokenize()
            program = Parser(tokens).parse_program()
            # if expression -> eval and print
            if program.statements and type(program.statements[-1]).__name__ == "ExprStatement":
                last_expr = program.statements.pop()
                self.interpreter.run(program)
                val = self.interpreter.evaluate(last_expr.expr, self.interpreter.globals)
                if val is not None:
                    print(self.interpreter.stringify(val))
            else:
                self.interpreter.run(program)
            return False

        except LangSyntaxError as e:
            if any(err in str(e) for err in ["TokenType.EOF", "Unterminated string"]):
                return True
            print(f"Syntax Error: {e}", file=sys.stderr)
            return False
        except LangRuntimeError as e:
            print(f"Runtime Error: {e}", file=sys.stderr)
            return False