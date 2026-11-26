"""Tokenizador de SQL."""

from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = {
    "CREATE",
    "TABLE",
    "DROP",
    "INSERT",
    "INTO",
    "VALUES",
    "SELECT",
    "FROM",
    "WHERE",
    "UPDATE",
    "SET",
    "DELETE",
    "PRIMARY",
    "KEY",
    "AND",
    "OR",
    "BETWEEN",
    "ORDER",
    "BY",
    "ASC",
    "DESC",
    "NULL",
    "TRUE",
    "FALSE",
}


@dataclass
class Token:
    """Unidad léxica producida por el lexer."""

    kind: str
    value: str


class Lexer:
    """Convierte texto SQL en una lista de tokens."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.length = len(text)

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < self.length:
            ch = self.text[self.pos]

            if ch.isspace():
                self.pos += 1
                continue

            # Comentarios SQL de línea (-- ...)
            if ch == "-" and self.pos + 1 < self.length and self.text[self.pos + 1] == "-":
                while self.pos < self.length and self.text[self.pos] != "\n":
                    self.pos += 1
                continue

            # Cadenas entre comillas simples o dobles
            if ch in {"'", '"'}:
                tokens.append(self._read_string(ch))
                continue

            # Números enteros o reales (incluyendo negativos como -5 o -3.14)
            if ch.isdigit() or (
                ch == "-" and self.pos + 1 < self.length and self.text[self.pos + 1].isdigit()
            ):
                tokens.append(self._read_number())
                continue

            # Identificadores o palabras clave
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_word())
                continue

            # Operadores de dos caracteres
            two = self.text[self.pos : self.pos + 2]
            if two in {"<=", ">=", "!=", "<>"}:
                norm = "!=" if two == "<>" else two
                tokens.append(Token("OP", norm))
                self.pos += 2
                continue

            # Operadores y símbolos de un carácter
            if ch in {"=", "<", ">"}:
                tokens.append(Token("OP", ch))
                self.pos += 1
                continue

            symbols = {
                "(": "LPAREN",
                ")": "RPAREN",
                ",": "COMMA",
                ";": "SEMI",
                "*": "STAR",
            }
            if ch in symbols:
                tokens.append(Token(symbols[ch], ch))
                self.pos += 1
                continue

            raise SyntaxError(f"Carácter inesperado en SQL: {ch!r} en posición {self.pos}")

        tokens.append(Token("EOF", ""))
        return tokens

    def _read_string(self, quote: str) -> Token:
        self.pos += 1
        chars: list[str] = []
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch == quote:
                self.pos += 1
                return Token("STRING", "".join(chars))
            chars.append(ch)
            self.pos += 1
        raise SyntaxError("Cadena de texto sin cerrar")

    def _read_number(self) -> Token:
        start = self.pos
        if self.text[self.pos] == "-":
            self.pos += 1
        has_dot = False
        while self.pos < self.length:
            ch = self.text[self.pos]
            if ch.isdigit():
                self.pos += 1
            elif ch == "." and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break
        return Token("NUMBER", self.text[start : self.pos])

    def _read_word(self) -> Token:
        start = self.pos
        while self.pos < self.length and (
            self.text[self.pos].isalnum() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        word = self.text[start : self.pos]
        upper = word.upper()
        if upper in KEYWORDS:
            return Token("KEYWORD", upper)
        return Token("IDENT", word)