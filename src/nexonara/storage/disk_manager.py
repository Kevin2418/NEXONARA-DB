"""Lectura y escritura de páginas en archivos de la base de datos."""

from __future__ import annotations

from pathlib import Path

from nexonara.storage.page import Page


class DiskManager:
    """Gestiona el archivo físico donde se almacenan las páginas.

    TODO: abrir/crear el archivo, leer y escribir páginas por número.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def read_page(self, page_id: int) -> Page:
        raise NotImplementedError

    def write_page(self, page: Page) -> None:
        raise NotImplementedError
