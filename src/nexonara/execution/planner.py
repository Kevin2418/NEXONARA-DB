"""Planificador: transforma un AST en un plan de ejecución."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexonara.catalog.catalog import Catalog
from nexonara.sql.ast import (
    BetweenExpr,
    ComparisonExpr,
    CreateTableStmt,
    DeleteStmt,
    DropTableStmt,
    InsertStmt,
    SelectStmt,
    Statement,
    UpdateStmt,
)


@dataclass
class Plan:
    """Plan lógico/físico para el ejecutor."""

    statement: Statement
    access_method: str = "DIRECT"  # "AVL_PK", "AVL_RANGE", "SEQ_SCAN", "DIRECT"
    index_key: Any = None
    range_low: Any = None
    range_high: Any = None


class Planner:
    """Genera un plan óptimo consultando el catálogo y la clave primaria indexada."""

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog

    def plan(self, statement: Statement) -> Plan:
        if isinstance(statement, (CreateTableStmt, DropTableStmt, InsertStmt)):
            return Plan(statement=statement, access_method="DIRECT")

        if isinstance(statement, (SelectStmt, UpdateStmt, DeleteStmt)):
            schema = self.catalog.get_table(statement.table_name)
            pk_name = schema.pk_column.name.lower()
            where = statement.where

            if isinstance(where, ComparisonExpr) and where.column.lower() == pk_name:
                if where.op == "=":
                    return Plan(
                        statement=statement,
                        access_method="AVL_PK",
                        index_key=where.value,
                    )
                if where.op in {">", ">="}:
                    return Plan(
                        statement=statement,
                        access_method="AVL_RANGE",
                        range_low=where.value,
                        range_high=None,
                    )
                if where.op in {"<", "<="}:
                    return Plan(
                        statement=statement,
                        access_method="AVL_RANGE",
                        range_low=None,
                        range_high=where.value,
                    )

            if isinstance(where, BetweenExpr) and where.column.lower() == pk_name:
                return Plan(
                    statement=statement,
                    access_method="AVL_RANGE",
                    range_low=where.low,
                    range_high=where.high,
                )

            return Plan(statement=statement, access_method="SEQ_SCAN")

        raise ValueError(f"Tipo de sentencia no planificable: {type(statement).__name__}")