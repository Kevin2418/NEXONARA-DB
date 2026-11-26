"""Pruebas de las páginas con directorio de slots."""

import pytest

from nexonara.storage.page import Page, PageFullError


def test_insertar_y_leer_registro() -> None:
    page = Page.empty(0)

    rid = page.insert(b"hola")

    assert rid == 0
    assert page.get(rid) == b"hola"
    assert page.slot_count == 1
    assert page.dirty is True


def test_varios_registros_y_reutilizar_slot() -> None:
    page = Page.empty(0)
    assert page.insert(b"uno") == 0
    assert page.insert(b"dos") == 1
    assert page.insert(b"tres") == 2

    page.delete(1)
    with pytest.raises(KeyError):
        page.get(1)

    assert page.insert(b"nuevo") == 1
    assert page.get(1) == b"nuevo"
    assert page.slot_count == 3


def test_compaccion_recupera_huecos() -> None:
    page = Page.empty(0)
    for _ in range(3):
        page.insert(b"x" * 1000)

    page.delete(1)
    assert page.free_space < 2000

    assert page.insert(b"y" * 2000) == 1
    assert page.get(0) == b"x" * 1000
    assert page.get(1) == b"y" * 2000
    assert page.get(2) == b"x" * 1000


def test_pagina_llena() -> None:
    page = Page.empty(0)
    for _ in range(4):
        page.insert(b"x" * 1000)

    with pytest.raises(PageFullError):
        page.insert(b"x" * 1000)


def test_serializacion_conserva_registros() -> None:
    page = Page.empty(7)
    page.insert(b"primero")
    page.insert(b"segundo")

    copia = Page(7, page.data)

    assert copia.get(0) == b"primero"
    assert copia.get(1) == b"segundo"
