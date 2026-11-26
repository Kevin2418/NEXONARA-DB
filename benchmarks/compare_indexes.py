"""Compara el comportamiento de BST, AVL y rojo-negro.

Uso:
    python benchmarks/compare_indexes.py
"""

from __future__ import annotations

import random
import time

from nexonara.index import AVLIndex, BSTIndex, Index, RedBlackIndex

INDEX_CLASSES = (BSTIndex, AVLIndex, RedBlackIndex)


def measure(cls: type[Index], keys: list[int]) -> tuple[int, float, float]:
    index = cls()

    start = time.perf_counter()
    for key in keys:
        index.insert(key, (0, key))
    insert_time = time.perf_counter() - start

    start = time.perf_counter()
    for key in keys:
        index.search(key)
    search_time = time.perf_counter() - start

    return index.height, insert_time, search_time


def main() -> None:
    n = 2000
    random_keys = list(range(n))
    random.Random(42).shuffle(random_keys)
    sorted_keys = list(range(n))

    print(f"Comparación de índices con n={n}\n")
    print(f"{'Datos':<12} {'Índice':<14} {'Altura':>8} {'Inserción':>12} {'Búsqueda':>12}")
    print("-" * 62)

    for label, keys in (("aleatorio", random_keys), ("ordenado", sorted_keys)):
        for cls in INDEX_CLASSES:
            height, insert_time, search_time = measure(cls, keys)
            print(
                f"{label:<12} {cls.__name__:<14} {height:>8} "
                f"{insert_time:>10.4f} s {search_time:>10.4f} s"
            )

    print(
        "\nCon datos ordenados el BST se degenera: su altura es n y la "
        "búsqueda pasa a ser O(n).\nAVL y rojo-negro mantienen altura "
        "logarítmica."
    )


if __name__ == "__main__":
    main()
