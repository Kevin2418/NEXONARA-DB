"""Catálogo de metadatos: tablas, columnas y esquemas."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any

from nexonara.types.values import VALID_TYPES, cast_value


@dataclass
class Column:
    """Definición de una columna."""

    name: str
    type_name: str
    primary_key: bool = False

    def __post_init__(self) -> None:
        self.type_name = self.type_name.upper()
        if self.type_name not in VALID_TYPES:
            raise ValueError(f"Tipo de columna inválido: {self.type_name}")


@dataclass
class TableSchema:
    """Esquema de una tabla relacional."""

    name: str
    columns: list[Column] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.columns:
            raise ValueError("Una tabla debe tener al menos una columna")
        seen: set[str] = set()
        for col in self.columns:
            key = col.name.lower()
            if key in seen:
                raise ValueError(f"Columna duplicada '{col.name}' en tabla '{self.name}'")
            seen.add(key)

        pk_cols = [c for c in self.columns if c.primary_key]
        if len(pk_cols) > 1:
            raise ValueError("Solo se admite una columna PRIMARY KEY por tabla")
        if not pk_cols:
            # Si no se especifica PRIMARY KEY explícita, la primera columna actúa como PK.
            self.columns[0].primary_key = True

    @property
    def pk_column(self) -> Column:
        for col in self.columns:
            if col.primary_key:
                return col
        return self.columns[0]

    @property
    def pk_index(self) -> int:
        for idx, col in enumerate(self.columns):
            if col.primary_key:
                return idx
        return 0

    def column_index(self, name: str) -> int:
        target = name.lower()
        for idx, col in enumerate(self.columns):
            if col.name.lower() == target:
                return idx
        raise KeyError(f"La columna '{name}' no existe en '{self.name}'")

    def validate_row(self, raw_values: list[Any]) -> list[Any]:
        """Valida longitud, tipos y que la clave primaria no sea NULL."""
        if len(raw_values) != len(self.columns):
            raise ValueError(
                f"Se esperaban {len(self.columns)} valores, se recibieron {len(raw_values)}"
            )
        clean: list[Any] = []
        for col, val in zip(self.columns, raw_values):
            casted = cast_value(val, col.type_name)
            if col.primary_key and casted is None:
                raise ValueError(f"La clave primaria '{col.name}' no puede ser NULL")
            clean.append(casted)
        return clean

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "columns": [
                {
                    "name": c.name,
                    "type_name": c.type_name,
                    "primary_key": c.primary_key,
                }
                for c in self.columns
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableSchema:
        cols = [
            Column(
                name=c["name"],
                type_name=c["type_name"],
                primary_key=bool(c.get("primary_key", False)),
            )
            for c in data["columns"]
        ]
        return cls(name=data["name"], columns=cols)


class Catalog:
    """Registro persistente de las tablas existentes en la base de datos."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._catalog_path = self.data_dir / "catalog.json"
        self._tables: dict[str, TableSchema] = {}
        self._load()

    def _load(self) -> None:
        if not self._catalog_path.exists():
            return
        with self._catalog_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        for item in payload.get("tables", []):
            schema = TableSchema.from_dict(item)
            self._tables[schema.name.lower()] = schema

    def save(self) -> None:
        """Persiste el catálogo en disco mediante reemplazo atómico."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {"tables": [t.to_dict() for t in self._tables.values()]}
        tmp_path = self._catalog_path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self._catalog_path)

    def create_table(self, schema: TableSchema) -> None:
        key = schema.name.lower()
        if key in self._tables:
            raise ValueError(f"La tabla '{schema.name}' ya existe")
        self._tables[key] = schema
        self.save()

    def drop_table(self, name: str) -> TableSchema:
        key = name.lower()
        if key not in self._tables:
            raise KeyError(f"La tabla '{name}' no existe")
        removed = self._tables.pop(key)
        self.save()
        return removed

    def get_table(self, name: str) -> TableSchema:
        key = name.lower()
        if key not in self._tables:
            raise KeyError(f"La tabla '{name}' no existe")
        return self._tables[key]

    def has_table(self, name: str) -> bool:
        return name.lower() in self._tables

    def list_tables(self) -> list[str]:
        return [t.name for t in self._tables.values()]