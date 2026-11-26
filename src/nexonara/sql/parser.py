"""Parser de SQL: convierte tokens en un AST."""

from __future__ import annotations

from nexonara.sql.ast import Statement
from nexonara.sql.lexer import Lexer


class Parser:
    """Analizador sintáctico de consultas SQL.

    TODO: implementar un parser descendente recursivo.
    """

    def __init__(self, text: str) -> None:
        self.lexer = Lexer(text)

    def parse(self) -> Statement:
        raise NotImplementedError
