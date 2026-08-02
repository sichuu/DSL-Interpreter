"""Lexer/Tokenizer for the Data Analysis DSL."""
from enum import Enum, auto


class TokenType(Enum):
    LOAD = auto()
    FILTER = auto()
    SORT = auto()
    GROUPBY = auto()
    AVERAGE = auto()
    SUM = auto()
    COUNT = auto()
    MIN = auto()
    MAX = auto()
    SELECT = auto()
    EXPORT = auto()
    SHOW = auto()
    DESCRIBE = auto()
    ASC = auto()
    DESC = auto()
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    OP = auto()
    COMMA = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    'LOAD': TokenType.LOAD,
    'FILTER': TokenType.FILTER,
    'SORT': TokenType.SORT,
    'GROUPBY': TokenType.GROUPBY,
    'AVERAGE': TokenType.AVERAGE,
    'AVG': TokenType.AVERAGE,
    'MEAN': TokenType.AVERAGE,
    'SUM': TokenType.SUM,
    'COUNT': TokenType.COUNT,
    'MIN': TokenType.MIN,
    'MAX': TokenType.MAX,
    'SELECT': TokenType.SELECT,
    'EXPORT': TokenType.EXPORT,
    'SAVE': TokenType.EXPORT,
    'SHOW': TokenType.SHOW,
    'PRINT': TokenType.SHOW,
    'DESCRIBE': TokenType.DESCRIBE,
    'ASC': TokenType.ASC,
    'DESC': TokenType.DESC,
}

TYPE_TO_CANONICAL = {
    TokenType.AVERAGE: 'AVERAGE',
    TokenType.SUM: 'SUM',
    TokenType.COUNT: 'COUNT',
    TokenType.MIN: 'MIN',
    TokenType.MAX: 'MAX',
}


class Token:
    __slots__ = ('type', 'value', 'line')

    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


class LexerError(Exception):
    def __init__(self, message, line):
        super().__init__(f"Lexer error on line {line}: {message}")
        self.line = line


class Lexer:
    """Converts raw DSL source text into a flat stream of Tokens."""

    def __init__(self, source: str):
        self.source = source
        self.line = 1
        self.tokens = []

    def tokenize(self):
        for line_no, raw_line in enumerate(self.source.split('\n'), start=1):
            self.line = line_no
            line = raw_line.split('#', 1)[0]  # strip comments
            self._tokenize_line(line)
            if self.tokens and self.tokens[-1].type != TokenType.NEWLINE:
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line))
        self.tokens.append(Token(TokenType.EOF, None, self.line))
        return self.tokens

    def _tokenize_line(self, line: str):
        i, n = 0, len(line)
        while i < n:
            ch = line[i]

            if ch.isspace():
                i += 1
                continue

            if ch in ('"', "'"):
                quote = ch
                j = i + 1
                buf = []
                while j < n and line[j] != quote:
                    buf.append(line[j])
                    j += 1
                if j >= n:
                    raise LexerError("unterminated string literal", self.line)
                self.tokens.append(Token(TokenType.STRING, ''.join(buf), self.line))
                i = j + 1
                continue

            if ch == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line))
                i += 1
                continue

            two = line[i:i + 2]
            if two in ('>=', '<=', '==', '!='):
                self.tokens.append(Token(TokenType.OP, two, self.line))
                i += 2
                continue

            if ch in ('>', '<', '='):
                self.tokens.append(Token(TokenType.OP, ch, self.line))
                i += 1
                continue

            if ch.isdigit() or (ch == '-' and i + 1 < n and line[i + 1].isdigit()):
                j = i + 1
                while j < n and (line[j].isdigit() or line[j] == '.'):
                    j += 1
                text = line[i:j]
                num = float(text) if '.' in text else int(text)
                self.tokens.append(Token(TokenType.NUMBER, num, self.line))
                i = j
                continue

            if ch.isalpha() or ch == '_':
                j = i + 1
                while j < n and (line[j].isalnum() or line[j] in '_.'):
                    j += 1
                word = line[i:j]
                upper = word.upper()
                if upper in KEYWORDS:
                    self.tokens.append(Token(KEYWORDS[upper], upper, self.line))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, word, self.line))
                i = j
                continue

            raise LexerError(f"unexpected character {ch!r}", self.line)
