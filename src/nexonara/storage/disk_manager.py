"""Acceso físico: lectura y escritura de páginas en un archivo."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType

from nexonara.storage.page import PAGE_SIZE, Page


class DiskManager:
    """Administra el archivo de la base de datos página por página.

    Cada página ocupa ``PAGE_SIZE`` bytes y su posición en el archivo se
    calcula como ``page_id * PAGE_SIZE``. Esto permite acceso directo sin
    leer todo el archivo.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "r+b" if self.db_path.exists() else "w+b"
        self._file = self.db_path.open(mode)

    def __enter__(self) -> DiskManager:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Descarga los cambios pendientes y cierra el archivo."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def page_count(self) -> int:
        """Cantidad de páginas que ocupa el archivo."""
        size = self.db_path.stat().st_size
        return (size + PAGE_SIZE - 1) // PAGE_SIZE

    def read_page(self, page_id: int) -> Page:
        """Lee una página por su número."""
        if page_id < 0:
            raise ValueError("El id de página no puede ser negativo")

        self._file.seek(page_id * PAGE_SIZE)
        data = self._file.read(PAGE_SIZE)
        if not data:
            raise IndexError(f"La página {page_id} no existe")
        if len(data) < PAGE_SIZE:
            # Recupera una página incompleta rellenando con ceros.
            data += bytes(PAGE_SIZE - len(data))
        return Page(page_id, data)

    def write_page(self, page: Page) -> None:
        """Escribe una página completa en su posición del archivo."""
        if page.page_id < 0:
            raise ValueError("El id de página no puede ser negativo")
        if len(page.data) != PAGE_SIZE:
            raise ValueError(f"La página debe medir exactamente {PAGE_SIZE} bytes")

        self._file.seek(page.page_id * PAGE_SIZE)
        self._file.write(page.data)
        self._file.flush()
        page.dirty = False

    def allocate_page(self) -> Page:
        """Reserva una página nueva al final del archivo."""
        page = Page.empty(self.page_count())
        self.write_page(page)
        return page

    def sync(self) -> None:
        """Fuerza la escritura de los datos al sistema operativo."""
        self._file.flush()
