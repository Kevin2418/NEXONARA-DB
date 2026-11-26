"""Páginas de tamaño fijo con un directorio de slots.

Formato de una página (4096 bytes, little-endian):

    +-------------+----------------------------+----------------------+
    | slots (2 B) | directorio de slots (4 B)  | espacio libre        |
    +-------------+----------------------------+----------------------+
                                                         ^
                                          los registros crecen desde
                                          el final hacia el inicio

Cada entrada del directorio guarda el offset y la longitud de un registro.
Una longitud de 0 indica un slot libre o eliminado.

El identificador de un registro (RID) es el índice de su slot. Los RID no
cambian cuando se compacta la página, porque el directorio conserva su orden.
"""

from __future__ import annotations

import struct

PAGE_SIZE = 4096
HEADER_SIZE = 2
SLOT_SIZE = 4

_SLOT_COUNT = struct.Struct("<H")
_SLOT_ENTRY = struct.Struct("<HH")


class PageFullError(Exception):
    """La página no tiene espacio suficiente para el registro."""


class Page:
    """Página con almacenamiento de registros por slots."""

    def __init__(self, page_id: int, data: bytes | bytearray | None = None) -> None:
        if page_id < 0:
            raise ValueError("El id de página no puede ser negativo")
        if data is None:
            self.data = bytearray(PAGE_SIZE)
        else:
            if len(data) != PAGE_SIZE:
                raise ValueError(f"La página debe medir exactamente {PAGE_SIZE} bytes")
            self.data = bytearray(data)
        self.page_id = page_id
        self.dirty = False

    @classmethod
    def empty(cls, page_id: int) -> Page:
        """Crea una página vacía."""
        return cls(page_id)

    @property
    def slot_count(self) -> int:
        """Cantidad de slots del directorio, incluidos los eliminados."""
        return _SLOT_COUNT.unpack_from(self.data, 0)[0]

    @property
    def free_space(self) -> int:
        """Bytes contiguos disponibles antes del registro más bajo."""
        return self._record_start() - self._directory_end()

    def insert(self, payload: bytes) -> int:
        """Inserta un registro y devuelve su RID (índice del slot)."""
        if not payload:
            raise ValueError("El registro no puede estar vacío")

        slot_id = self._find_free_slot()
        is_new_slot = slot_id is None
        if slot_id is None:
            slot_id = self.slot_count

        if not self._fits(len(payload), is_new_slot):
            self.compact()
            if not self._fits(len(payload), is_new_slot):
                raise PageFullError(
                    f"No caben {len(payload)} bytes en la página {self.page_id}"
                )

        if is_new_slot:
            self._set_slot_count(self.slot_count + 1)

        start = self._record_start() - len(payload)
        self.data[start : start + len(payload)] = payload
        self._set_slot(slot_id, start, len(payload))
        self.dirty = True
        return slot_id

    def get(self, slot_id: int) -> bytes:
        """Devuelve el registro almacenado en un slot."""
        offset, length = self._slot(slot_id)
        if length == 0:
            raise KeyError(f"El slot {slot_id} está libre")
        return bytes(self.data[offset : offset + length])

    def delete(self, slot_id: int) -> None:
        """Libera un slot sin mover los demás registros."""
        self._slot(slot_id)  # valida que el slot exista
        self._set_slot(slot_id, 0, 0)
        self.dirty = True

    def compact(self) -> None:
        """Reorganiza los registros para recuperar huecos internos."""
        records: list[bytes | None] = []
        for slot_id in range(self.slot_count):
            offset, length = self._slot(slot_id)
            records.append(
                bytes(self.data[offset : offset + length]) if length else None
            )

        new_data = bytearray(PAGE_SIZE)
        _SLOT_COUNT.pack_into(new_data, 0, len(records))
        cursor = PAGE_SIZE
        for slot_id, record in enumerate(records):
            if record is None:
                continue
            cursor -= len(record)
            new_data[cursor : cursor + len(record)] = record
            _SLOT_ENTRY.pack_into(
                new_data, HEADER_SIZE + slot_id * SLOT_SIZE, cursor, len(record)
            )

        self.data = new_data
        self.dirty = True

    def _fits(self, payload_size: int, is_new_slot: bool) -> bool:
        slot_count = self.slot_count + (1 if is_new_slot else 0)
        directory_end = HEADER_SIZE + slot_count * SLOT_SIZE
        return self._record_start() - payload_size >= directory_end

    def _find_free_slot(self) -> int | None:
        for slot_id in range(self.slot_count):
            _, length = self._slot(slot_id)
            if length == 0:
                return slot_id
        return None

    def _record_start(self) -> int:
        start = PAGE_SIZE
        for slot_id in range(self.slot_count):
            offset, length = self._slot(slot_id)
            if length:
                start = min(start, offset)
        return start

    def _directory_end(self) -> int:
        return HEADER_SIZE + self.slot_count * SLOT_SIZE

    def _set_slot_count(self, count: int) -> None:
        _SLOT_COUNT.pack_into(self.data, 0, count)

    def _slot(self, slot_id: int) -> tuple[int, int]:
        if not 0 <= slot_id < self.slot_count:
            raise IndexError(f"El slot {slot_id} está fuera de rango")
        return _SLOT_ENTRY.unpack_from(self.data, HEADER_SIZE + slot_id * SLOT_SIZE)

    def _set_slot(self, slot_id: int, offset: int, length: int) -> None:
        _SLOT_ENTRY.pack_into(
            self.data, HEADER_SIZE + slot_id * SLOT_SIZE, offset, length
        )

    def __repr__(self) -> str:
        return (
            f"Page(page_id={self.page_id}, slots={self.slot_count}, "
            f"free={self.free_space})"
        )
