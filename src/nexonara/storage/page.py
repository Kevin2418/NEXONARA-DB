"""Páginas de tamaño fijo, unidad básica de almacenamiento."""

from __future__ import annotations

from dataclasses import dataclass

PAGE_SIZE = 4096


@dataclass
class Page:
    """Representa una página de datos.

    TODO: añadir flags de modificación y serialización de registros.
    """

    page_id: int
    data: bytearray

    @classmethod
    def empty(cls, page_id: int) -> "Page":
        """Crea una página vacía del tamaño configurado."""
        return cls(page_id=page_id, data=bytearray(PAGE_SIZE))
