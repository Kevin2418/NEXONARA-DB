"""Árbol AVL: BST balanceado por altura.

Después de cada inserción o eliminación, la diferencia de altura entre los
subárboles de un nodo es como máximo 1. Cuando se rompe esa condición, se
aplican rotaciones simples o dobles.
"""

from __future__ import annotations

from nexonara.index.base import Entry, Index, Key, RID


class _Node:
    __slots__ = ("key", "rids", "left", "right", "height")

    def __init__(self, key: Key, rid: RID) -> None:
        self.key = key
        self.rids: list[RID] = [rid]
        self.left: _Node | None = None
        self.right: _Node | None = None
        self.height = 1


def _height(node: _Node | None) -> int:
    return node.height if node is not None else 0


def _update(node: _Node) -> None:
    node.height = 1 + max(_height(node.left), _height(node.right))


def _balance_factor(node: _Node) -> int:
    return _height(node.left) - _height(node.right)


def _rotate_left(x: _Node) -> _Node:
    y = x.right
    assert y is not None
    x.right = y.left
    y.left = x
    _update(x)
    _update(y)
    return y


def _rotate_right(x: _Node) -> _Node:
    y = x.left
    assert y is not None
    x.left = y.right
    y.right = x
    _update(x)
    _update(y)
    return y


def _rebalance(node: _Node) -> _Node:
    balance = _balance_factor(node)

    if balance > 1:
        assert node.left is not None
        if _balance_factor(node.left) < 0:
            node.left = _rotate_left(node.left)
        return _rotate_right(node)

    if balance < -1:
        assert node.right is not None
        if _balance_factor(node.right) > 0:
            node.right = _rotate_right(node.right)
        return _rotate_left(node)

    return node


class AVLIndex(Index):
    """Índice mediante un árbol AVL."""

    def __init__(self) -> None:
        self._root: _Node | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def height(self) -> int:
        return _height(self._root)

    def insert(self, key: Key, rid: RID) -> None:
        self._root, inserted = self._insert(self._root, key, rid)
        if inserted:
            self._size += 1

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

        def walk(node: _Node | None) -> None:
            if node is None:
                return
            if start is None or node.key >= start:
                walk(node.left)

            if (start is None or node.key >= start) and (
                end is None or node.key <= end
            ):
                for rid in node.rids:
                    result.append((node.key, rid))

            if end is None or node.key <= end:
                walk(node.right)

        walk(self._root)
        return result

    def validate(self) -> None:
        count = 0

        def walk(
            node: _Node | None, low: Key | None, high: Key | None
        ) -> int:
            nonlocal count
            if node is None:
                return 0

            assert node.rids, "Todo nodo debe tener al menos un RID"
            if low is not None:
                assert node.key > low, "Violación del orden del AVL"
            if high is not None:
                assert node.key < high, "Violación del orden del AVL"
            assert node.height == 1 + max(
                _height(node.left), _height(node.right)
            ), "Altura almacenada incorrecta"

            left_height = walk(node.left, low, node.key)
            right_height = walk(node.right, node.key, high)
            assert abs(left_height - right_height) <= 1, "AVL desbalanceado"

            count += len(node.rids)
            return node.height

        walk(self._root, None, None)
        assert count == self._size, "El tamaño no coincide con las entradas"

    def _insert(
        self, node: _Node | None, key: Key, rid: RID
    ) -> tuple[_Node, bool]:
        if node is None:
            return _Node(key, rid), True

        if key == node.key:
            if rid in node.rids:
                return node, False
            node.rids.append(rid)
            return node, True

        if key < node.key:
            node.left, inserted = self._insert(node.left, key, rid)
        else:
            node.right, inserted = self._insert(node.right, key, rid)

        if not inserted:
            return node, False

        _update(node)
        return _rebalance(node), True

    def _delete(
        self, node: _Node | None, key: Key, rid: RID | None
    ) -> tuple[_Node | None, int]:
        if node is None:
            return None, 0

        if key < node.key:
            node.left, removed = self._delete(node.left, key, rid)
            if removed:
                _update(node)
                node = _rebalance(node)
            return node, removed

        if key > node.key:
            node.right, removed = self._delete(node.right, key, rid)
            if removed:
                _update(node)
                node = _rebalance(node)
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
        _update(successor)
        return _rebalance(successor), removed

    def _remove_min(self, node: _Node) -> tuple[_Node, _Node | None]:
        """Devuelve ``(nodo_mínimo, subárbol_sin_el_mínimo)``."""
        if node.left is None:
            return node, node.right

        minimum, node.left = self._remove_min(node.left)
        _update(node)
        return minimum, _rebalance(node)
