"""Índice propio en árbol autobalanceado AVL (sin librerías externas).

Convención de equilibrio:
    balance_factor = height(right) - height(left) in {-1, 0, +1}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AVLNode:
    """Nodo del árbol AVL que mapea una clave primaria a su RID (page_id, slot_id)."""

    key: Any
    rid: tuple[int, int]
    left: AVLNode | None = None
    right: AVLNode | None = None
    height: int = 1


class AVLTree:
    """Árbol autobalanceado AVL con operaciones en O(log n)."""

    def __init__(self) -> None:
        self.root: AVLNode | None = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    @property
    def size(self) -> int:
        return self._size

    def clear(self) -> None:
        self.root = None
        self._size = 0

    @staticmethod
    def _height(node: AVLNode | None) -> int:
        return node.height if node is not None else 0

    def _update_height(self, node: AVLNode) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node: AVLNode | None) -> int:
        if node is None:
            return 0
        return self._height(node.right) - self._height(node.left)

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """Rotación Simple Izquierda (RSI)."""
        y = x.right
        assert y is not None
        t2 = y.left

        y.left = x
        x.right = t2

        self._update_height(x)
        self._update_height(y)
        return y

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """Rotación Simple Derecha (RSD)."""
        x = y.left
        assert x is not None
        t2 = x.right

        x.right = y
        y.left = t2

        self._update_height(y)
        self._update_height(x)
        return x

    def _rebalance(self, node: AVLNode) -> AVLNode:
        self._update_height(node)
        bf = self._balance_factor(node)

        # Desbalanceo a la derecha (+2): RSI o RDD
        if bf > 1:
            if self._balance_factor(node.right) < 0:
                assert node.right is not None
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        # Desbalanceo a la izquierda (-2): RSD o RDI
        if bf < -1:
            if self._balance_factor(node.left) > 0:
                assert node.left is not None
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        return node

    def search(self, key: Any) -> tuple[int, int] | None:
        """Busca una clave en O(log n) y retorna su RID o None si no existe."""
        curr = self.root
        while curr is not None:
            if key == curr.key:
                return curr.rid
            curr = curr.left if key < curr.key else curr.right
        return None

    def insert(self, key: Any, rid: tuple[int, int]) -> None:
        """Inserta (key, rid) en O(log n). Lanza ValueError si la clave ya existe."""
        self.root = self._insert(self.root, key, rid)
        self._size += 1

    def _insert(self, node: AVLNode | None, key: Any, rid: tuple[int, int]) -> AVLNode:
        if node is None:
            return AVLNode(key=key, rid=rid)
        if key == node.key:
            raise ValueError(f"Clave primaria duplicada: {key!r}")
        if key < node.key:
            node.left = self._insert(node.left, key, rid)
        else:
            node.right = self._insert(node.right, key, rid)
        return self._rebalance(node)

    def update(self, key: Any, new_rid: tuple[int, int]) -> None:
        """Actualiza el RID asociado a una clave existente en O(log n)."""
        curr = self.root
        while curr is not None:
            if key == curr.key:
                curr.rid = new_rid
                return
            curr = curr.left if key < curr.key else curr.right
        raise KeyError(f"Clave no encontrada en el índice: {key!r}")

    def delete(self, key: Any) -> bool:
        """Elimina una clave en O(log n). Retorna True si existía y se borró."""
        self.root, deleted = self._delete(self.root, key)
        if deleted:
            self._size -= 1
        return deleted

    def _delete(self, node: AVLNode | None, key: Any) -> tuple[AVLNode | None, bool]:
        if node is None:
            return None, False

        if key < node.key:
            node.left, deleted = self._delete(node.left, key)
        elif key > node.key:
            node.right, deleted = self._delete(node.right, key)
        else:
            deleted = True
            if node.left is None:
                return node.right, True
            if node.right is None:
                return node.left, True
            # Nodo con 2 hijos: reemplaza por el menor del subárbol derecho (sucesor)
            successor = self._min_node(node.right)
            node.key = successor.key
            node.rid = successor.rid
            node.right, _ = self._delete(node.right, successor.key)

        if not deleted:
            return node, False
        return self._rebalance(node), True

    @staticmethod
    def _min_node(node: AVLNode) -> AVLNode:
        curr = node
        while curr.left is not None:
            curr = curr.left
        return curr

    def inorder(self) -> list[tuple[Any, tuple[int, int]]]:
        """Recorrido in-order ascendente en O(n)."""
        result: list[tuple[Any, tuple[int, int]]] = []
        self._inorder(self.root, result)
        return result

    def _inorder(
        self, node: AVLNode | None, acc: list[tuple[Any, tuple[int, int]]]
    ) -> None:
        if node is None:
            return
        self._inorder(node.left, acc)
        acc.append((node.key, node.rid))
        self._inorder(node.right, acc)

    def range_query(
        self, low: Any | None = None, high: Any | None = None
    ) -> list[tuple[Any, tuple[int, int]]]:
        """Devuelve pares (key, rid) ordenados dentro de [low, high] en O(log n + k)."""
        result: list[tuple[Any, tuple[int, int]]] = []
        self._range(self.root, low, high, result)
        return result

    def _range(
        self,
        node: AVLNode | None,
        low: Any | None,
        high: Any | None,
        acc: list[tuple[Any, tuple[int, int]]],
    ) -> None:
        if node is None:
            return
        if low is None or node.key > low:
            self._range(node.left, low, high, acc)
        if (low is None or node.key >= low) and (high is None or node.key <= high):
            acc.append((node.key, node.rid))
        if high is None or node.key < high:
            self._range(node.right, low, high, acc)

    def is_balanced(self) -> bool:
        """Verifica que todo el árbol cumpla la invariante AVL (útil en pruebas)."""
        return self._check_balanced(self.root)[0]

    def _check_balanced(self, node: AVLNode | None) -> tuple[bool, int]:
        if node is None:
            return True, 0
        ok_l, h_l = self._check_balanced(node.left)
        ok_r, h_r = self._check_balanced(node.right)
        balanced = ok_l and ok_r and abs(h_r - h_l) <= 1
        return balanced, 1 + max(h_l, h_r)