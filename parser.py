from dataclasses import dataclass
from lexer import TokenType, LangSyntaxError


@dataclass
class Program:
    statements: list


@dataclass
class FunctionDef:
    name: str
    params: list
    body: list


@dataclass
class Return:
    value: object


@dataclass
class If:
    condition: object
    then_body: list
    else_body: list


@dataclass
class While:
    condition: object
    body: list


@dataclass
class Assign:
    name: str
    op: str
    value: object


@dataclass
class ExprStatement:
    expr: object


@dataclass
class BinaryOp:
    op: str
    left: object
    right: object


@dataclass
class UnaryOp:
    op: str
    operand: object


@dataclass
class Call:
    callee: str
    args: list


@dataclass
class Identifier:
    name: str


@dataclass
class NumberLiteral:
    value: object


@dataclass
class StringLiteral:
    value: str


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def check(self, type_):
        return self.current().type == type_

    def match(self, *types):
        if self.current().type in types:
            tok = self.current()
            self.pos += 1
            return tok
        return None

    def expect(self, type_, message=None):
        if self.check(type_):
            tok = self.current()
            self.pos += 1
            return tok
        got = self.current()
        raise LangSyntaxError(message or f"Expected {type_} but got {got.type} at line {got.line}")

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE):
            self.pos += 1

    def parse_program(self):
        statements = []
        self.skip_newlines()
        while not self.check(TokenType.EOF):
            statements.append(self.parse_statement())
            self.skip_newlines()
        return Program(statements)

    def parse_block(self, terminators):
        statements = []
        self.skip_newlines()
        while self.current().type not in terminators:
            statements.append(self.parse_statement())
            self.skip_newlines()
        return statements

    def parse_statement(self):
        if self.check(TokenType.FUN):
            return self.parse_function_def()
        if self.check(TokenType.IF):
            return self.parse_if()
        if self.check(TokenType.WHILE):
            return self.parse_while()
        if self.check(TokenType.RETURN):
            return self.parse_return()
        if self.check(TokenType.IDENT) and self.tokens[self.pos + 1].type in (
            TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN
        ):
            return self.parse_assignment()
        expr = self.parse_expression()
        return ExprStatement(expr)

    def parse_function_def(self):
        self.expect(TokenType.FUN)
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.LPAREN)
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        body = self.parse_block((TokenType.END,))
        self.expect(TokenType.END)
        return FunctionDef(name_tok.value, params, body)

    def parse_if(self):
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        then_body = self.parse_block((TokenType.ELSE, TokenType.END))
        else_body = []
        if self.match(TokenType.ELSE):
            else_body = self.parse_block((TokenType.END,))
        self.expect(TokenType.END)
        return If(condition, then_body, else_body)

    def parse_while(self):
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        body = self.parse_block((TokenType.END,))
        self.expect(TokenType.END)
        return While(condition, body)

    def parse_return(self):
        self.expect(TokenType.RETURN)
        if self.current().type in (TokenType.NEWLINE, TokenType.EOF, TokenType.END):
            return Return(None)
        value = self.parse_expression()
        return Return(value)

    def parse_assignment(self):
        name_tok = self.expect(TokenType.IDENT)
        op_tok = self.match(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN)
        op_map = {
            TokenType.ASSIGN: '=',
            TokenType.PLUS_ASSIGN: '+=',
            TokenType.MINUS_ASSIGN: '-=',
        }
        value = self.parse_expression()
        return Assign(name_tok.value, op_map[op_tok.type], value)

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinaryOp('or', left, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.match(TokenType.AND):
            right = self.parse_equality()
            left = BinaryOp('and', left, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.current().type in (TokenType.EQ, TokenType.NEQ):
            op_tok = self.match(TokenType.EQ, TokenType.NEQ)
            op = '==' if op_tok.type == TokenType.EQ else '!='
            right = self.parse_relational()
            left = BinaryOp(op, left, right)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.current().type in (TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            op_tok = self.match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE)
            op_map = {
                TokenType.LT: '<',
                TokenType.LTE: '<=',
                TokenType.GT: '>',
                TokenType.GTE: '>=',
            }
            right = self.parse_additive()
            left = BinaryOp(op_map[op_tok.type], left, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self.match(TokenType.PLUS, TokenType.MINUS)
            op = '+' if op_tok.type == TokenType.PLUS else '-'
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)
            op_map = {
                TokenType.STAR: '*',
                TokenType.SLASH: '/',
                TokenType.PERCENT: '%',
            }
            right = self.parse_unary()
            left = BinaryOp(op_map[op_tok.type], left, right)
        return left

    def parse_unary(self):
        if self.match(TokenType.MINUS):
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        if self.match(TokenType.NOT):
            operand = self.parse_unary()
            return UnaryOp('not', operand)
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while self.check(TokenType.LPAREN) and isinstance(expr, Identifier):
            self.expect(TokenType.LPAREN)
            args = []
            if not self.check(TokenType.RPAREN):
                args.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    args.append(self.parse_expression())
            self.expect(TokenType.RPAREN)
            expr = Call(expr.name, args)
        return expr

    def parse_primary(self):
        tok = self.current()
        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLiteral(tok.value)
        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(tok.value)
        if tok.type == TokenType.IDENT:
            self.pos += 1
            return Identifier(tok.value)
        if tok.type == TokenType.LPAREN:
            self.pos += 1
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        raise LangSyntaxError(f"Unexpected token {tok.type} at line {tok.line}")
