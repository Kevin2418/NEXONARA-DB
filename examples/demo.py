"""Demo de integración: almacenamiento + índices.

Guarda filas en una página real, construye los tres índices sobre la misma
clave y muestra búsquedas y recorridos por rango.

Uso:
    python examples/demo.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from nexonara.index import AVLIndex, BSTIndex, Index, RedBlackIndex
from nexonara.storage.buffer_pool import BufferPool
from nexonara.storage.disk_manager import DiskManager

ROWS = [
    (30, "Ana"),
    (10, "Luis"),
    (20, "Marta"),
    (40, "Pedro"),
    (25, "Sofía"),
]


def store_rows(pool: BufferPool) -> tuple[int, list[tuple[int, tuple[int, int]]]]:
    """Guarda las filas en una página y devuelve sus RID."""
    page = pool.new_page()
    indexed: list[tuple[int, tuple[int, int]]] = []

    for key, name in ROWS:
        rid = (page.page_id, page.insert(name.encode("utf-8")))
        indexed.append((key, rid))

    pool.unpin_page(page.page_id)
    return page.page_id, indexed


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "demo.db"

        with DiskManager(db_path) as disk:
            with BufferPool(disk, capacity=8) as pool:
                page_id, indexed = store_rows(pool)

                print("NEXONARA-DB: demo de almacenamiento e índices")
                print(f"Archivo temporal: {db_path}")
                print(f"Página: {page_id} | filas: {len(indexed)}\n")

                for cls in (BSTIndex, AVLIndex, RedBlackIndex):
                    index: Index = cls()
                    for key, rid in indexed:
                        index.insert(key, rid)
                    index.validate()

                    print(f"{cls.__name__} (altura {index.height})")

                    page = pool.get_page(page_id)
                    for key in (25, 30):
                        rids = index.search(key)
                        values = [page.get(rid[1]).decode("utf-8") for rid in rids]
                        print(f"  search({key}) = {rids} -> {values}")

                    print("  range_scan(20, 30):")
                    for key, rid in index.range_scan(20, 30):
                        value = page.get(rid[1]).decode("utf-8")
                        print(f"    {key}: {value} {rid}")
                    pool.unpin_page(page_id)
                    print()

                print("validate() correcto en los tres índices.")


if __name__ == "__main__":
    main()
