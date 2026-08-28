from dataclasses import dataclass
from enum import Enum, auto


class LangSyntaxError(Exception):
    pass


class TokenType(Enum):
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()
    FUN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    END = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    'fun': TokenType.FUN,
    'return': TokenType.RETURN,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'end': TokenType.END,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
}


@dataclass
class Token:
    type: TokenType
    value: object
    line: int


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.length = len(source)
        self.tokens = []

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx >= self.length:
            return ''
        return self.source[idx]

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def add(self, type_, value=None, line=None):
        self.tokens.append(Token(type_, value, line if line is not None else self.line))

    def tokenize(self):
        while self.pos < self.length:
            ch = self.peek()
            if ch == '\n':
                self.advance()
                self.add(TokenType.NEWLINE)
                continue
            if ch in ' \t\r':
                self.advance()
                continue
            if ch == '#':
                while self.pos < self.length and self.peek() != '\n':
                    self.advance()
                continue
            if ch.isdigit():
                self.read_number()
                continue
            if ch == '"':
                self.read_string()
                continue
            if ch.isalpha() or ch == '_':
                self.read_ident()
                continue
            self.read_operator()
        self.add(TokenType.EOF)
        return self.tokens

    def read_number(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and self.peek().isdigit():
            self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            self.advance()
            while self.pos < self.length and self.peek().isdigit():
                self.advance()
            value = float(self.source[start:self.pos])
        else:
            value = int(self.source[start:self.pos])
        self.add(TokenType.NUMBER, value, start_line)

    def read_string(self):
        start_line = self.line
        self.advance()
        chars = []
        while self.pos < self.length and self.peek() != '"':
            ch = self.advance()
            if ch == '\\':
                if self.pos >= self.length:
                    raise LangSyntaxError(f"Unterminated string at line {start_line}")
                esc = self.advance()
                mapping = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
                chars.append(mapping.get(esc, esc))
            else:
                chars.append(ch)
        if self.pos >= self.length:
            raise LangSyntaxError(f"Unterminated string at line {start_line}")
        self.advance()
        self.add(TokenType.STRING, ''.join(chars), start_line)

    def read_ident(self):
        start_line = self.line
        start = self.pos
        while self.pos < self.length and (self.peek().isalnum() or self.peek() == '_'):
            self.advance()
        text = self.source[start:self.pos]
        type_ = KEYWORDS.get(text, TokenType.IDENT)
        value = text if type_ == TokenType.IDENT else None
        self.add(type_, value, start_line)

    def read_operator(self):
        start_line = self.line
        two = self.peek() + self.peek(1)
        mapping2 = {
            '==': TokenType.EQ,
            '!=': TokenType.NEQ,
            '<=': TokenType.LTE,
            '>=': TokenType.GTE,
            '+=': TokenType.PLUS_ASSIGN,
            '-=': TokenType.MINUS_ASSIGN,
        }
        if two in mapping2:
            self.advance()
            self.advance()
            self.add(mapping2[two], None, start_line)
            return
        one = self.peek()
        mapping1 = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '%': TokenType.PERCENT,
            '=': TokenType.ASSIGN,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            ',': TokenType.COMMA,
        }
        if one in mapping1:
            self.advance()
            self.add(mapping1[one], None, start_line)
            return
        raise LangSyntaxError(f"Unexpected character {one!r} at line {start_line}")
