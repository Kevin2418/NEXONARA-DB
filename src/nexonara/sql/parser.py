"""Parser de SQL: convierte tokens en un AST."""

from __future__ import annotations

from typing import Any

from nexonara.sql.ast import (
    BetweenExpr,
    ColumnDef,
    ComparisonExpr,
    CreateTableStmt,
    DeleteStmt,
    DropTableStmt,
    Expr,
    InsertStmt,
    LogicalExpr,
    SelectStmt,
    Statement,
    UpdateStmt,
)
from nexonara.sql.lexer import Lexer, Token


class Parser:
    """Analizador sintáctico descendente recursivo."""

    def __init__(self, text: str) -> None:
        self.tokens = Lexer(text).tokenize()
        self.idx = 0

    def _peek(self) -> Token:
        return self.tokens[self.idx]

    def _advance(self) -> Token:
        tok = self.tokens[self.idx]
        if tok.kind != "EOF":
            self.idx += 1
        return tok

    def _match_keyword(self, kw: str) -> bool:
        tok = self._peek()
        if tok.kind == "KEYWORD" and tok.value == kw:
            self._advance()
            return True
        return False

    def _expect_keyword(self, kw: str) -> None:
        if not self._match_keyword(kw):
            tok = self._peek()
            raise SyntaxError(f"Se esperaba '{kw}', se encontró {tok.value!r}")

    def _expect_kind(self, kind: str) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise SyntaxError(f"Se esperaba token {kind}, se encontró {tok.kind} ({tok.value!r})")
        return self._advance()

    def _expect_name(self) -> str:
        tok = self._peek()
        if tok.kind in {"IDENT", "KEYWORD"}:
            return self._advance().value
        raise SyntaxError(f"Se esperaba un identificador, se encontró {tok.value!r}")

    def parse(self) -> Statement:
        if self._peek().kind == "EOF":
            raise SyntaxError("Consulta vacía")

        if self._match_keyword("CREATE"):
            stmt = self._parse_create()
        elif self._match_keyword("DROP"):
            stmt = self._parse_drop()
        elif self._match_keyword("INSERT"):
            stmt = self._parse_insert()
        elif self._match_keyword("SELECT"):
            stmt = self._parse_select()
        elif self._match_keyword("UPDATE"):
            stmt = self._parse_update()
        elif self._match_keyword("DELETE"):
            stmt = self._parse_delete()
        else:
            raise SyntaxError(f"Sentencia no soportada: {self._peek().value!r}")

        # Punto y coma final opcional
        if self._peek().kind == "SEMI":
            self._advance()
        if self._peek().kind != "EOF":
            raise SyntaxError(f"Tokens inesperados al final: {self._peek().value!r}")
        return stmt

    def _parse_create(self) -> CreateTableStmt:
        self._expect_keyword("TABLE")
        table_name = self._expect_name()
        self._expect_kind("LPAREN")
        cols: list[ColumnDef] = []
        while True:
            col_name = self._expect_name()
            col_type = self._expect_name().upper()
            is_pk = False
            if self._match_keyword("PRIMARY"):
                self._expect_keyword("KEY")
                is_pk = True
            cols.append(ColumnDef(name=col_name, type_name=col_type, primary_key=is_pk))
            if self._peek().kind == "COMMA":
                self._advance()
                continue
            break
        self._expect_kind("RPAREN")
        return CreateTableStmt(table_name=table_name, columns=cols)

    def _parse_drop(self) -> DropTableStmt:
        self._expect_keyword("TABLE")
        table_name = self._expect_name()
        return DropTableStmt(table_name=table_name)

    def _parse_insert(self) -> InsertStmt:
        self._expect_keyword("INTO")
        table_name = self._expect_name()
        self._expect_keyword("VALUES")
        self._expect_kind("LPAREN")
        values: list[Any] = []
        while True:
            values.append(self._parse_literal())
            if self._peek().kind == "COMMA":
                self._advance()
                continue
            break
        self._expect_kind("RPAREN")
        return InsertStmt(table_name=table_name, values=values)

    def _parse_select(self) -> SelectStmt:
        cols: list[str] | None = None
        if self._peek().kind == "STAR":
            self._advance()
        else:
            cols = []
            while True:
                cols.append(self._expect_name())
                if self._peek().kind == "COMMA":
                    self._advance()
                    continue
                break

        self._expect_keyword("FROM")
        table_name = self._expect_name()

        where_expr: Expr | None = None
        if self._match_keyword("WHERE"):
            where_expr = self._parse_or()

        order_by: str | None = None
        order_desc = False
        if self._match_keyword("ORDER"):
            self._expect_keyword("BY")
            order_by = self._expect_name()
            if self._match_keyword("DESC"):
                order_desc = True
            else:
                self._match_keyword("ASC")

        return SelectStmt(
            table_name=table_name,
            columns=cols,
            where=where_expr,
            order_by=order_by,
            order_desc=order_desc,
        )

    def _parse_update(self) -> UpdateStmt:
        table_name = self._expect_name()
        self._expect_keyword("SET")
        assignments: dict[str, Any] = {}
        while True:
            col = self._expect_name()
            op = self._expect_kind("OP")
            if op.value != "=":
                raise SyntaxError(f"Se esperaba '=' en SET, se encontró {op.value!r}")
            assignments[col] = self._parse_literal()
            if self._peek().kind == "COMMA":
                self._advance()
                continue
            break

        where_expr: Expr | None = None
        if self._match_keyword("WHERE"):
            where_expr = self._parse_or()

        return UpdateStmt(table_name=table_name, assignments=assignments, where=where_expr)

    def _parse_delete(self) -> DeleteStmt:
        self._expect_keyword("FROM")
        table_name = self._expect_name()
        where_expr: Expr | None = None
        if self._match_keyword("WHERE"):
            where_expr = self._parse_or()
        return DeleteStmt(table_name=table_name, where=where_expr)

    # --- Precedencia WHERE: OR -> AND -> comparación / BETWEEN ---

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._match_keyword("OR"):
            right = self._parse_and()
            left = LogicalExpr(op="OR", left=left, right=right)
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_predicate()
        while self._match_keyword("AND"):
            right = self._parse_predicate()
            left = LogicalExpr(op="AND", left=left, right=right)
        return left

    def _parse_predicate(self) -> Expr:
        col = self._expect_name()
        if self._match_keyword("BETWEEN"):
            low = self._parse_literal()
            self._expect_keyword("AND")
            high = self._parse_literal()
            return BetweenExpr(column=col, low=low, high=high)

        op = self._expect_kind("OP").value
        val = self._parse_literal()
        return ComparisonExpr(column=col, op=op, value=val)

    def _parse_literal(self) -> Any:
        tok = self._peek()
        if tok.kind == "NUMBER":
            self._advance()
            return float(tok.value) if "." in tok.value else int(tok.value)
        if tok.kind == "STRING":
            self._advance()
            return tok.value
        if tok.kind == "KEYWORD":
            if tok.value == "TRUE":
                self._advance()
                return True
            if tok.value == "FALSE":
                self._advance()
                return False
            if tok.value == "NULL":
                self._advance()
                return None
        raise SyntaxError(f"Valor literal inesperado: {tok.value!r}")