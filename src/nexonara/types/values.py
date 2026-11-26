"""Valores tipados y serialización binaria de tuplas."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

VALID_TYPES = {"INTEGER", "REAL", "TEXT", "BOOLEAN"}


def cast_value(raw: Any, type_name: str) -> Any:
    """Convierte y valida un valor según el tipo declarado en el esquema."""
    if raw is None:
        return None

    t = type_name.upper()
    if t == "INTEGER":
        if isinstance(raw, bool):
            raise TypeError(f"Se esperaba INTEGER, se recibió BOOLEAN ({raw})")
        if isinstance(raw, int):
            return raw
        s = str(raw).strip()
        if s.lstrip("-").isdigit():
            return int(s)
        raise TypeError(f"Se esperaba INTEGER, se recibió: {raw!r}")

    if t == "REAL":
        if isinstance(raw, bool):
            raise TypeError(f"Se esperaba REAL, se recibió BOOLEAN ({raw})")
        if isinstance(raw, (int, float)):
            return float(raw)
        try:
            return float(str(raw).strip())
        except ValueError as exc:
            raise TypeError(f"Se esperaba REAL, se recibió: {raw!r}") from exc

    if t == "BOOLEAN":
        if isinstance(raw, bool):
            return raw
        s = str(raw).strip().lower()
        if s in {"true", "1"}:
            return True
        if s in {"false", "0"}:
            return False
        raise TypeError(f"Se esperaba BOOLEAN (true/false), se recibió: {raw!r}")

    if t == "TEXT":
        return str(raw)

    raise ValueError(f"Tipo de dato no soportado: {type_name}")


def serialize_row(values: list[Any]) -> bytes:
    """Codifica una lista de valores de celda en bytes UTF-8 para una página."""
    return json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def deserialize_row(payload: bytes) -> list[Any]:
    """Decodifica los bytes almacenados en una página a una lista de valores."""
    return json.loads(payload.decode("utf-8"))


@dataclass
class Value:
    """Envoltorio tipado de una celda."""

    value: Any
    type_name: str = "TEXT"

    def __post_init__(self) -> None:
        self.type_name = self.type_name.upper()
        self.value = cast_value(self.value, self.type_name)

    def is_null(self) -> bool:
        return self.value is None