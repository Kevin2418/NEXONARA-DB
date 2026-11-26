"""Buffer pool: caché de páginas con reemplazo LRU y pinning.

``get_page`` y ``new_page`` fijan (pin) la página para que no sea expulsada
mientras quien la usa sigue trabajando con ella. Después de terminar, hay que
llamar a ``unpin_page``. Una página solo puede desalojarse si su contador de
pins es cero.
"""

from __future__ import annotations

from collections import OrderedDict
from types import TracebackType

from nexonara.storage.disk_manager import DiskManager
from nexonara.storage.page import Page


class BufferPoolFullError(Exception):
    """No hay páginas sin fijar que se puedan desalojar."""


class BufferPool:
    """Mantiene páginas en memoria con una capacidad máxima."""

    def __init__(self, disk_manager: DiskManager, capacity: int = 64) -> None:
        if capacity <= 0:
            raise ValueError("La capacidad del buffer debe ser mayor que cero")
        self.disk_manager = disk_manager
        self.capacity = capacity
        self._pages: OrderedDict[int, Page] = OrderedDict()
        self._pins: dict[int, int] = {}

    def __enter__(self) -> BufferPool:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def __len__(self) -> int:
        return len(self._pages)

    @property
    def cached_pages(self) -> tuple[int, ...]:
        """Ids de las páginas cargadas, de la menos a la más reciente."""
        return tuple(self._pages)

    def pin_count(self, page_id: int) -> int:
        """Cantidad de usuarios que tienen fijada una página."""
        return self._pins.get(page_id, 0)

    def get_page(self, page_id: int) -> Page:
        """Devuelve una página y la fija en memoria."""
        if page_id in self._pages:
            page = self._pages[page_id]
            self._pages.move_to_end(page_id)
            self._pins[page_id] += 1
            return page

        if len(self._pages) >= self.capacity:
            self._evict()

        page = self.disk_manager.read_page(page_id)
        self._pages[page_id] = page
        self._pins[page_id] = 1
        return page

    def new_page(self) -> Page:
        """Reserva una página nueva y la deja fijada en el buffer."""
        if len(self._pages) >= self.capacity:
            self._evict()

        page = self.disk_manager.allocate_page()
        self._pages[page.page_id] = page
        self._pins[page.page_id] = 1
        return page

    def unpin_page(self, page_id: int) -> None:
        """Suelta una página para que pueda ser desalojada."""
        pins = self._pins.get(page_id, 0)
        if pins == 0:
            raise ValueError(f"La página {page_id} no está fijada")
        self._pins[page_id] = pins - 1

    def flush_page(self, page_id: int) -> None:
        """Escribe una página si tiene cambios pendientes."""
        try:
            page = self._pages[page_id]
        except KeyError as exc:
            raise ValueError(f"La página {page_id} no está en el buffer") from exc

        if page.dirty:
            self.disk_manager.write_page(page)

    def flush_all(self) -> None:
        """Escribe todas las páginas sucias del buffer."""
        for page in self._pages.values():
            if page.dirty:
                self.disk_manager.write_page(page)

    def close(self) -> None:
        """Vuelca el buffer y cierra el archivo de disco."""
        self.flush_all()
        self.disk_manager.close()

    def _evict(self) -> None:
        """Expulsa la página sin fijar menos usada recientemente."""
        victim_id = next(
            (
                page_id
                for page_id in self._pages
                if self._pins.get(page_id, 0) == 0
            ),
            None,
        )
        if victim_id is None:
            raise BufferPoolFullError("Todas las páginas del buffer están fijadas")

        page = self._pages[victim_id]
        if page.dirty:
            self.disk_manager.write_page(page)
        del self._pages[victim_id]
        del self._pins[victim_id]
