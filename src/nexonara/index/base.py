"""Interfaz común para índices ordenados."""

from __future__ import annotations

from abc import ABC, abstractmethod

Key = int | str
RID = tuple[int, int]
Entry = tuple[Key, RID]


class Index(ABC):
    """Índice ordenado que asocia claves con RIDs.

    Un RID identifica un registro dentro del almacenamiento:
    ``(page_id, slot_id)``.

    Todas las claves de una misma instancia deben ser comparables entre sí,
    es decir, del mismo tipo (todas enteras o todas texto).
    """

    @abstractmethod
    def insert(self, key: Key, rid: RID) -> None:
        """Inserta la pareja ``(key, rid)``.

        Si la pareja ya existe, la operación no hace nada.
        """

    @abstractmethod
    def search(self, key: Key) -> list[RID]:
        """Devuelve una copia de los RID asociados a ``key``."""

    @abstractmethod
    def delete(self, key: Key, rid: RID | None = None) -> bool:
        """Elimina entradas del índice.

        Si ``rid`` es ``None``, elimina todas las entradas de ``key``.
        Si se indica ``rid``, elimina solo esa pareja.
        Devuelve ``True`` si se eliminó al menos una entrada.
        """

    @abstractmethod
    def range_scan(
        self, start: Key | None = None, end: Key | None = None
    ) -> list[Entry]:
        """Devuelve las entradas con ``start <= key <= end``, en orden.

        ``None`` significa "sin límite" en ese extremo.
        """

    def items(self) -> list[Entry]:
        """Devuelve todas las entradas en orden."""
        return self.range_scan()

    def is_empty(self) -> bool:
        return len(self) == 0

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, (int, str)):
            return False
        return bool(self.search(key))

    @abstractmethod
    def __len__(self) -> int:
        """Cantidad de entradas (pares clave-RID), no de nodos."""

    @property
    @abstractmethod
    def height(self) -> int:
        """Altura del árbol; un árbol vacío tiene altura 0."""

    @abstractmethod
    def validate(self) -> None:
        """Verifica las invariantes del índice.

        Lanza una excepción ``AssertionError`` si el árbol es inconsistente.
        Es útil en pruebas y para demostrar el funcionamiento interno.
        """
