"""Pruebas unitarias del índice AVL, tipos y catálogo persistente."""

from pathlib import Path

import pytest

from nexonara.catalog.catalog import Catalog, Column, TableSchema
from nexonara.index.avl import AVLTree
from nexonara.types.values import deserialize_row, serialize_row


def test_avl_insert_rotations_search_range_and_delete() -> None:
    tree = AVLTree()
    # Inserción secuencial (forzaría degeneración en un ABB normal)
    for k in range(1, 51):
        tree.insert(k, (0, k - 1))

    assert len(tree) == 50
    assert tree.is_balanced()
    assert tree.search(25) == (0, 24)
    assert tree.search(999) is None

    # Rango [10, 15]
    rango = tree.range_query(10, 15)
    assert [k for k, _ in rango] == [10, 11, 12, 13, 14, 15]

    # Eliminación de varios nodos y verificación de invariante AVL
    for k in [1, 25, 30, 10, 49, 50]:
        assert tree.delete(k) is True
    assert tree.delete(999) is False
    assert len(tree) == 44
    assert tree.is_balanced()
    assert [k for k, _ in tree.inorder()] == sorted(
        set(range(1, 51)) - {1, 25, 30, 10, 49, 50}
    )


def test_avl_rejects_duplicate_key() -> None:
    tree = AVLTree()
    tree.insert(1, (0, 0))
    with pytest.raises(ValueError, match="duplicada"):
        tree.insert(1, (0, 1))


def test_catalog_persistence_and_row_validation(tmp_path: Path) -> None:
    cat = Catalog(tmp_path)
    schema = TableSchema(
        name="estudiantes",
        columns=[
            Column("id", "INTEGER", primary_key=True),
            Column("nombre", "TEXT"),
            Column("promedio", "REAL"),
            Column("activo", "BOOLEAN"),
        ],
    )
    cat.create_table(schema)

    clean = schema.validate_row(["1", "Ana", "4.5", "true"])
    assert clean == [1, "Ana", 4.5, True]
    assert deserialize_row(serialize_row(clean)) == clean

    # Reiniciar catálogo desde disco
    reloaded = Catalog(tmp_path)
    assert reloaded.has_table("estudiantes")
    t = reloaded.get_table("estudiantes")
    assert t.pk_column.name == "id"
    assert [c.type_name for c in t.columns] == ["INTEGER", "TEXT", "REAL", "BOOLEAN"]

    reloaded.drop_table("estudiantes")
    assert not Catalog(tmp_path).has_table("estudiantes")