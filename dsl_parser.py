"""Recursive-descent parser: Tokens -> AST."""
from dataclasses import dataclass, field
from typing import List, Optional, Any

from lexer import TokenType, TYPE_TO_CANONICAL


# ---------- AST Nodes ----------

@dataclass
class LoadStmt:
    filename: str
    line: int


@dataclass
class FilterStmt:
    column: str
    op: str
    value: Any
    line: int


@dataclass
class SortStmt:
    column: str
    order: str  # 'ASC' | 'DESC'
    line: int


@dataclass
class GroupByStmt:
    column: str
    line: int


@dataclass
class AggregateStmt:
    func: str  # 'AVERAGE' | 'SUM' | 'COUNT' | 'MIN' | 'MAX'
    column: str
    line: int


@dataclass
class SelectStmt:
    columns: List[str]
    line: int


@dataclass
class ExportStmt:
    filename: str
    line: int


@dataclass
class ShowStmt:
    n: Optional[int]
    line: int


@dataclass
class DescribeStmt:
    line: int


class ParserError(Exception):
    def __init__(self, message, line):
        super().__init__(f"Parse error on line {line}: {message}")
        self.line = line


# ---------- Parser ----------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, type_):
        return self.peek().type == type_

    def expect(self, type_, msg=None):
        if not self.check(type_):
            tok = self.peek()
            raise ParserError(msg or f"expected {type_.name}, got {tok.type.name} ({tok.value!r})", tok.line)
        return self.advance()

    def parse(self):
        statements = []
        while not self.check(TokenType.EOF):
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue
            statements.append(self.parse_statement())
            if not self.check(TokenType.EOF):
                self.expect(TokenType.NEWLINE, "expected end of line")
        return statements

    def parse_statement(self):
        tok = self.peek()
        dispatch = {
            TokenType.LOAD: self.parse_load,
            TokenType.FILTER: self.parse_filter,
            TokenType.SORT: self.parse_sort,
            TokenType.GROUPBY: self.parse_groupby,
            TokenType.SELECT: self.parse_select,
            TokenType.EXPORT: self.parse_export,
            TokenType.SHOW: self.parse_show,
        }
        if tok.type in dispatch:
            return dispatch[tok.type]()
        if tok.type in (TokenType.AVERAGE, TokenType.SUM, TokenType.COUNT,
                        TokenType.MIN, TokenType.MAX):
            return self.parse_aggregate()
        if tok.type == TokenType.DESCRIBE:
            self.advance()
            return DescribeStmt(line=tok.line)
        raise ParserError(f"unexpected token {tok.type.name} ({tok.value!r})", tok.line)

    def parse_filename(self):
        tok = self.peek()
        if tok.type in (TokenType.STRING, TokenType.IDENTIFIER):
            self.advance()
            return str(tok.value)
        raise ParserError("expected a filename", tok.line)

    def parse_load(self):
        tok = self.advance()
        return LoadStmt(filename=self.parse_filename(), line=tok.line)

    def parse_filter(self):
        tok = self.advance()
        col = self.expect(TokenType.IDENTIFIER, "expected column name after FILTER").value
        op_tok = self.expect(TokenType.OP, "expected a comparison operator (>, <, >=, <=, ==, !=)")
        val_tok = self.peek()
        if val_tok.type not in (TokenType.NUMBER, TokenType.STRING, TokenType.IDENTIFIER):
            raise ParserError("expected a value after the operator", val_tok.line)
        self.advance()
        return FilterStmt(column=col, op=op_tok.value, value=val_tok.value, line=tok.line)

    def parse_sort(self):
        tok = self.advance()
        col = self.expect(TokenType.IDENTIFIER, "expected column name after SORT").value
        order = 'ASC'
        if self.check(TokenType.ASC):
            self.advance()
        elif self.check(TokenType.DESC):
            self.advance()
            order = 'DESC'
        return SortStmt(column=col, order=order, line=tok.line)

    def parse_groupby(self):
        tok = self.advance()
        col = self.expect(TokenType.IDENTIFIER, "expected column name after GROUPBY").value
        return GroupByStmt(column=col, line=tok.line)

    def parse_aggregate(self):
        tok = self.advance()
        func = TYPE_TO_CANONICAL[tok.type]
        col = self.expect(TokenType.IDENTIFIER, f"expected column name after {func}").value
        return AggregateStmt(func=func, column=col, line=tok.line)

    def parse_select(self):
        tok = self.advance()
        cols = [self.expect(TokenType.IDENTIFIER, "expected column name after SELECT").value]
        while self.check(TokenType.COMMA):
            self.advance()
            cols.append(self.expect(TokenType.IDENTIFIER, "expected column name after ','").value)
        return SelectStmt(columns=cols, line=tok.line)

    def parse_export(self):
        tok = self.advance()
        return ExportStmt(filename=self.parse_filename(), line=tok.line)

    def parse_show(self):
        tok = self.advance()
        n = self.advance().value if self.check(TokenType.NUMBER) else None
        return ShowStmt(n=n, line=tok.line)
