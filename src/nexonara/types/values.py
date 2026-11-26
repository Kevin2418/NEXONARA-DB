"""Valores tipados almacenados en las celdas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Value:
    """Valor de una celda.

    TODO: conversiones y comparaciones entre tipos.
    """

    value: Any

    def is_null(self) -> bool:
        return self.value is None
