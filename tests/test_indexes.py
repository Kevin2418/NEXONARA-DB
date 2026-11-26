"""Pruebas comunes para los índices BST, AVL y rojo-negro."""

from __future__ import annotations

import math
import random

import pytest

from nexonara.index import AVLIndex, BSTIndex, Index, RedBlackIndex

INDEX_CLASSES = (BSTIndex, AVLIndex, RedBlackIndex)


@pytest.fixture(params=INDEX_CLASSES, ids=lambda cls: cls.__name__)
def index(request: pytest.FixtureRequest) -> Index:
    return request.param()


def test_insertar_buscar_y_duplicados(index: Index) -> None:
    assert len(index) == 0
    assert index.height == 0

    index.insert(10, (0, 0))
    index.insert(10, (0, 1))
    index.insert(10, (0, 0))  # pareja duplicada: se ignora

    assert index.search(10) == [(0, 0), (0, 1)]
    assert index.search(99) == []
    assert len(index) == 2
    assert index.height == 1
    assert 10 in index
    assert 99 not in index
    index.validate()


def test_eliminar_rid_especifico_y_todas_las_entradas(index: Index) -> None:
    index.insert(5, (1, 0))
    index.insert(5, (1, 1))
    index.insert(3, (2, 0))
    index.insert(8, (3, 0))

    assert index.delete(5, (1, 0)) is True
    assert index.search(5) == [(1, 1)]

    assert index.delete(5) is True
    assert index.search(5) == []
    assert index.delete(5) is False

    assert len(index) == 2
    index.validate()


def test_range_scan_inclusivo_y_ordenado(index: Index) -> None:
    for key in (5, 2, 8, 1, 3, 7, 9):
        index.insert(key, (0, key))

    assert [key for key, _ in index.range_scan(2, 8)] == [2, 3, 5, 7, 8]
    assert [key for key, _ in index.range_scan()] == [1, 2, 3, 5, 7, 8, 9]
    assert [key for key, _ in index.range_scan(end=3)] == [1, 2, 3]
    assert [key for key, _ in index.range_scan(start=8)] == [8, 9]
    assert index.range_scan(9, 2) == []
    assert index.items() == index.range_scan()
    index.validate()


def test_claves_de_texto(index: Index) -> None:
    for position, key in enumerate(("pera", "manzana", "uva", "banana")):
        index.insert(key, (0, position))

    assert [key for key, _ in index.range_scan("banana", "pera")] == [
        "banana",
        "manzana",
        "pera",
    ]
    index.validate()


def test_eliminar_muchas_claves_ejercita_rotaciones(index: Index) -> None:
    keys = list(range(100))
    random.Random(42).shuffle(keys)
    for key in keys:
        index.insert(key, (0, key))

    index.validate()

    for key in keys[::2]:
        assert index.delete(key) is True
        index.validate()

    for key in keys[1::2]:
        assert index.delete(key) is True

    assert len(index) == 0
    assert index.height == 0
    assert index.range_scan() == []
    index.validate()


def test_operaciones_aleatorias_contra_modelo(index: Index) -> None:
    rng = random.Random(2026)
    model: dict[int, list[tuple[int, int]]] = {}

    for step in range(500):
        key = rng.randrange(30)
        action = rng.random()

        if action < 0.60:
            rid = (rng.randrange(4), rng.randrange(10))
            index.insert(key, rid)
            rids = model.setdefault(key, [])
            if rid not in rids:
                rids.append(rid)
        elif action < 0.85:
            rid = (rng.randrange(4), rng.randrange(10))
            rids = model.get(key, [])
            expected = rid in rids
            assert index.delete(key, rid) is expected
            if expected:
                rids.remove(rid)
            if not rids:
                model.pop(key, None)
        else:
            expected = key in model
            assert index.delete(key) is expected
            model.pop(key, None)

        if step % 20 == 0:
            expected_items = [
                (key, rid) for key in sorted(model) for rid in model[key]
            ]
            assert index.range_scan() == expected_items
            assert len(index) == len(expected_items)
            for model_key, rids in model.items():
                assert index.search(model_key) == rids
            index.validate()

    expected_items = [
        (key, rid) for key in sorted(model) for rid in model[key]
    ]
    assert index.range_scan() == expected_items
    assert len(index) == len(expected_items)
    index.validate()


def test_bst_se_degenera_con_insercion_ordenada() -> None:
    bst = BSTIndex()
    for key in range(100):
        bst.insert(key, (0, key))

    assert bst.height == 100
    bst.validate()


def test_avl_y_rojo_negro_mantienen_altura_logaritmica() -> None:
    n = 100
    limit = 2 * math.ceil(math.log2(n + 1))

    for cls in (AVLIndex, RedBlackIndex):
        tree = cls()
        for key in range(n):
            tree.insert(key, (0, key))

        assert tree.height <= limit
        tree.validate()
