"""Árbol binario de búsqueda (BST) sin balanceo.

Es la línea base didáctica: con inserciones aleatorias funciona bien, pero
con claves ordenadas se degenera en una lista y pasa de O(log n) a O(n).
"""

from __future__ import annotations

from nexonara.index.base import Entry, Index, Key, RID


class _Node:
    __slots__ = ("key", "rids", "left", "right")

    def __init__(self, key: Key, rid: RID) -> None:
        self.key = key
        self.rids: list[RID] = [rid]
        self.left: _Node | None = None
        self.right: _Node | None = None


class BSTIndex(Index):
    """Índice mediante un árbol binario de búsqueda sin balanceo."""

    def __init__(self) -> None:
        self._root: _Node | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def height(self) -> int:
        if self._root is None:
            return 0

        max_height = 0
        stack: list[tuple[_Node, int]] = [(self._root, 1)]
        while stack:
            node, depth = stack.pop()
            max_height = max(max_height, depth)
            if node.left is not None:
                stack.append((node.left, depth + 1))
            if node.right is not None:
                stack.append((node.right, depth + 1))
        return max_height

    def insert(self, key: Key, rid: RID) -> None:
        if self._root is None:
            self._root = _Node(key, rid)
            self._size = 1
            return

        node = self._root
        while True:
            if key == node.key:
                if rid not in node.rids:
                    node.rids.append(rid)
                    self._size += 1
                return

            if key < node.key:
                if node.left is None:
                    node.left = _Node(key, rid)
                    self._size += 1
                    return
                node = node.left
            else:
                if node.right is None:
                    node.right = _Node(key, rid)
                    self._size += 1
                    return
                node = node.right

    def search(self, key: Key) -> list[RID]:
        node = self._root
        while node is not None:
            if key == node.key:
                return list(node.rids)
            node = node.left if key < node.key else node.right
        return []

    def delete(self, key: Key, rid: RID | None = None) -> bool:
        self._root, removed = self._delete(self._root, key, rid)
        self._size -= removed
        return removed > 0

    def range_scan(
        self, start: Key | None = None, end: Key | None = None
    ) -> list[Entry]:
        if start is not None and end is not None and start > end:
            return []

        result: list[Entry] = []
        stack: list[_Node] = []
        node = self._root

        while stack or node is not None:
            while node is not None:
                if start is not None and node.key < start:
                    node = node.right
                else:
                    stack.append(node)
                    node = node.left

            if not stack:
                break

            node = stack.pop()
            if end is not None and node.key > end:
                break

            for rid in node.rids:
                result.append((node.key, rid))
            node = node.right

        return result

    def validate(self) -> None:
        count = 0

        def walk(
            node: _Node | None, low: Key | None, high: Key | None
        ) -> None:
            nonlocal count
            if node is None:
                return
            assert node.rids, "Todo nodo debe tener al menos un RID"
            if low is not None:
                assert node.key > low, "Violación del orden del BST"
            if high is not None:
                assert node.key < high, "Violación del orden del BST"
            count += len(node.rids)
            walk(node.left, low, node.key)
            walk(node.right, node.key, high)

        walk(self._root, None, None)
        assert count == self._size, "El tamaño no coincide con las entradas"

    def _delete(
        self, node: _Node | None, key: Key, rid: RID | None
    ) -> tuple[_Node | None, int]:
        if node is None:
            return None, 0

        if key < node.key:
            node.left, removed = self._delete(node.left, key, rid)
            return node, removed
        if key > node.key:
            node.right, removed = self._delete(node.right, key, rid)
            return node, removed

        if rid is None:
            removed = len(node.rids)
            node.rids.clear()
        else:
            if rid not in node.rids:
                return node, 0
            node.rids.remove(rid)
            removed = 1

        if node.rids:
            return node, removed

        if node.left is None:
            return node.right, removed
        if node.right is None:
            return node.left, removed

        successor, new_right = self._remove_min(node.right)
        successor.left = node.left
        successor.right = new_right
        return successor, removed

    def _remove_min(self, node: _Node) -> tuple[_Node, _Node | None]:
        """Devuelve ``(nodo_mínimo, subárbol_sin_el_mínimo)``."""
        if node.left is None:
            return node, node.right
        minimum, node.left = self._remove_min(node.left)
        return minimum, node
