"""Árbol rojo-negro: BST balanceado por color.

Propiedades que mantiene el árbol:

1. Cada nodo es rojo o negro.
2. La raíz es negra.
3. Un nodo rojo no puede tener hijos rojos.
4. Todo camino desde un nodo hasta sus hojas tiene la misma cantidad de
   nodos negros (misma altura negra).

Estas reglas garantizan una altura O(log n) con menos rotaciones que un AVL,
por lo que suele preferirse en estructuras con muchas inserciones y borrados.
"""

from __future__ import annotations

from nexonara.index.base import Entry, Index, Key, RID

RED = True
BLACK = False


class _Node:
    __slots__ = ("key", "rids", "color", "left", "right", "parent")

    def __init__(
        self,
        key: Key | None = None,
        rids: list[RID] | None = None,
        color: bool = BLACK,
    ) -> None:
        self.key = key
        self.rids: list[RID] = [] if rids is None else rids
        self.color = color
        # Se reemplazan por el centinela o por hijos reales al insertar.
        self.left: _Node = self
        self.right: _Node = self
        self.parent: _Node = self


class RedBlackIndex(Index):
    """Índice mediante un árbol rojo-negro."""

    def __init__(self) -> None:
        self._nil = _Node()
        self._nil.left = self._nil
        self._nil.right = self._nil
        self._nil.parent = self._nil
        self._root = self._nil
        self._size = 0

    def __len__(self) -> int:
        return self._size

    @property
    def height(self) -> int:
        def walk(node: _Node) -> int:
            if node is self._nil:
                return 0
            return 1 + max(walk(node.left), walk(node.right))

        return walk(self._root)

    def insert(self, key: Key, rid: RID) -> None:
        parent = self._nil
        node = self._root

        while node is not self._nil:
            parent = node
            if key == node.key:
                if rid not in node.rids:
                    node.rids.append(rid)
                    self._size += 1
                return
            node = node.left if key < node.key else node.right

        new_node = _Node(key, [rid], RED)
        new_node.left = self._nil
        new_node.right = self._nil
        new_node.parent = parent

        if parent is self._nil:
            self._root = new_node
        elif key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node

        self._size += 1
        self._insert_fixup(new_node)

    def search(self, key: Key) -> list[RID]:
        node = self._find_node(key)
        return [] if node is self._nil else list(node.rids)

    def delete(self, key: Key, rid: RID | None = None) -> bool:
        node = self._find_node(key)
        if node is self._nil:
            return False

        if rid is None:
            removed = len(node.rids)
            node.rids.clear()
        else:
            if rid not in node.rids:
                return False
            node.rids.remove(rid)
            removed = 1

        self._size -= removed
        if not node.rids:
            self._delete_node(node)
        return True

    def range_scan(
        self, start: Key | None = None, end: Key | None = None
    ) -> list[Entry]:
        if start is not None and end is not None and start > end:
            return []

        result: list[Entry] = []

        def walk(node: _Node) -> None:
            if node is self._nil:
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
        nil = self._nil
        assert nil.color == BLACK, "El centinela debe ser negro"
        assert nil.left is nil and nil.right is nil, "Centinela inconsistente"

        if self._root is nil:
            assert self._size == 0, "Árbol vacío con tamaño distinto de cero"
            return

        assert self._root.color == BLACK, "La raíz debe ser negra"
        assert self._root.parent is nil, "La raíz debe apuntar al centinela"

        count = 0

        def walk(
            node: _Node, low: Key | None, high: Key | None
        ) -> int:
            nonlocal count
            if node is nil:
                return 1

            assert node.rids, "Todo nodo debe tener al menos un RID"
            if low is not None:
                assert node.key > low, "Violación del orden del rojo-negro"
            if high is not None:
                assert node.key < high, "Violación del orden del rojo-negro"

            if node.color == RED:
                assert node.left.color == BLACK, "Nodo rojo con hijo rojo"
                assert node.right.color == BLACK, "Nodo rojo con hijo rojo"

            if node.left is not nil:
                assert node.left.parent is node, "Puntero parent incorrecto"
            if node.right is not nil:
                assert node.right.parent is node, "Puntero parent incorrecto"

            count += len(node.rids)
            left_black = walk(node.left, low, node.key)
            right_black = walk(node.right, node.key, high)
            assert left_black == right_black, "Alturas negras distintas"

            return left_black + (1 if node.color == BLACK else 0)

        walk(self._root, None, None)
        assert count == self._size, "El tamaño no coincide con las entradas"

    def _find_node(self, key: Key) -> _Node:
        node = self._root
        while node is not self._nil:
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right
        return self._nil

    def _insert_fixup(self, node: _Node) -> None:
        while node.parent.color == RED:
            parent = node.parent
            grandparent = parent.parent

            if parent is grandparent.left:
                uncle = grandparent.right
                if uncle.color == RED:
                    parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                else:
                    if node is parent.right:
                        node = parent
                        self._rotate_left(node)
                    node.parent.color = BLACK
                    node.parent.parent.color = RED
                    self._rotate_right(node.parent.parent)
            else:
                uncle = grandparent.left
                if uncle.color == RED:
                    parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent
                else:
                    if node is parent.left:
                        node = parent
                        self._rotate_right(node)
                    node.parent.color = BLACK
                    node.parent.parent.color = RED
                    self._rotate_left(node.parent.parent)

        self._root.color = BLACK

    def _delete_node(self, z: _Node) -> None:
        nil = self._nil
        y = z
        y_original_color = y.color

        if z.left is nil:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is nil:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right

            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y

            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color

        if y_original_color == BLACK:
            self._delete_fixup(x)

    def _delete_fixup(self, node: _Node) -> None:
        while node is not self._root and node.color == BLACK:
            parent = node.parent

            if node is parent.left:
                sibling = parent.right
                assert sibling is not self._nil, "Árbol rojo-negro inconsistente"

                if sibling.color == RED:
                    sibling.color = BLACK
                    parent.color = RED
                    self._rotate_left(parent)
                    sibling = parent.right

                if sibling.left.color == BLACK and sibling.right.color == BLACK:
                    sibling.color = RED
                    node = parent
                else:
                    if sibling.right.color == BLACK:
                        sibling.left.color = BLACK
                        sibling.color = RED
                        self._rotate_right(sibling)
                        sibling = parent.right

                    sibling.color = parent.color
                    parent.color = BLACK
                    sibling.right.color = BLACK
                    self._rotate_left(parent)
                    node = self._root
            else:
                sibling = parent.left
                assert sibling is not self._nil, "Árbol rojo-negro inconsistente"

                if sibling.color == RED:
                    sibling.color = BLACK
                    parent.color = RED
                    self._rotate_right(parent)
                    sibling = parent.left

                if sibling.right.color == BLACK and sibling.left.color == BLACK:
                    sibling.color = RED
                    node = parent
                else:
                    if sibling.left.color == BLACK:
                        sibling.right.color = BLACK
                        sibling.color = RED
                        self._rotate_left(sibling)
                        sibling = parent.left

                    sibling.color = parent.color
                    parent.color = BLACK
                    sibling.left.color = BLACK
                    self._rotate_right(parent)
                    node = self._root

        node.color = BLACK

    def _minimum(self, node: _Node) -> _Node:
        while node.left is not self._nil:
            node = node.left
        return node

    def _transplant(self, u: _Node, v: _Node) -> None:
        if u.parent is self._nil:
            self._root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _rotate_left(self, x: _Node) -> None:
        y = x.right
        x.right = y.left
        if y.left is not self._nil:
            y.left.parent = x

        y.parent = x.parent
        if x.parent is self._nil:
            self._root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y

    def _rotate_right(self, x: _Node) -> None:
        y = x.left
        x.left = y.right
        if y.right is not self._nil:
            y.right.parent = x

        y.parent = x.parent
        if x.parent is self._nil:
            self._root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y

        y.right = x
        x.parent = y
