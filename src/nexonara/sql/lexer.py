"""Tokenizador de SQL."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Token:
    """Unidad léxica producida por el lexer."""

    kind: str
    value: str


class Lexer:
    """Convierte texto SQL en una lista de tokens.

    TODO: implementar el análisis léxico.
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def tokenize(self) -> list[Token]:
        raise NotImplementedError
