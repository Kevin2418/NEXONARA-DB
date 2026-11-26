"""Caché de páginas en memoria (buffer pool)."""

from __future__ import annotations

from nexonara.storage.disk_manager import DiskManager
from nexonara.storage.page import Page


class BufferPool:
    """Mantiene páginas cargadas en memoria.

    TODO: implementar política de reemplazo, páginas sucias y pinning.
    """

    def __init__(self, disk_manager: DiskManager, capacity: int = 64) -> None:
        self.disk_manager = disk_manager
        self.capacity = capacity
        self._pages: dict[int, Page] = {}

    def get_page(self, page_id: int) -> Page:
        raise NotImplementedError
