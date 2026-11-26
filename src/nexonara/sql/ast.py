"""Nodos del árbol de sintaxis abstracta (AST) de las consultas SQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Statement:
    """Nodo base para cualquier sentencia SQL."""


@dataclass
class ColumnDef:
    """Definición de columna en CREATE TABLE."""

    name: str
    type_name: str
    primary_key: bool = False


@dataclass
class CreateTableStmt(Statement):
    """Sentencia CREATE TABLE."""

    table_name: str
    columns: list[ColumnDef]


@dataclass
class DropTableStmt(Statement):
    """Sentencia DROP TABLE."""

    table_name: str


@dataclass
class InsertStmt(Statement):
    """Sentencia INSERT INTO tabla VALUES (...)."""

    table_name: str
    values: list[Any]


# --- Expresiones WHERE ---


@dataclass
class Expr:
    """Nodo base de condición WHERE."""


@dataclass
class ComparisonExpr(Expr):
    """Comparación simple: columna op valor."""

    column: str
    op: str
    value: Any


@dataclass
class BetweenExpr(Expr):
    """Rango inclusivo: columna BETWEEN low AND high."""

    column: str
    low: Any
    high: Any


@dataclass
class LogicalExpr(Expr):
    """Combinación booleana: left AND/OR right."""

    op: str  # "AND" o "OR"
    left: Expr
    right: Expr


@dataclass
class SelectStmt(Statement):
    """Sentencia SELECT cols FROM tabla [WHERE expr] [ORDER BY col ASC|DESC]."""

    table_name: str
    columns: list[str] | None = None  # None equivale a '*'
    where: Expr | None = None
    order_by: str | None = None
    order_desc: bool = False


@dataclass
class UpdateStmt(Statement):
    """Sentencia UPDATE tabla SET col = val, ... [WHERE expr]."""

    table_name: str
    assignments: dict[str, Any]
    where: Expr | None = None


@dataclass
class DeleteStmt(Statement):
    """Sentencia DELETE FROM tabla [WHERE expr]."""

    table_name: str
    where: Expr | None = None