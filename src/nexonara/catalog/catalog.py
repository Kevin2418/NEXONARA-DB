"""Catálogo de metadatos: tablas, columnas y esquemas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Column:
    """Definición de una columna."""

    name: str
    type_name: str


@dataclass
class TableSchema:
    """Esquema de una tabla."""

    name: str
    columns: list[Column] = field(default_factory=list)


class Catalog:
    """Registro de las tablas existentes en la base de datos.

    TODO: persistir y recuperar esquemas desde disco.
    """

    def __init__(self) -> None:
        self._tables: dict[str, TableSchema] = {}

    def create_table(self, schema: TableSchema) -> None:
        raise NotImplementedError
