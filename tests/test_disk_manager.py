"""Pruebas del administrador de disco."""

import pytest

from nexonara.storage.disk_manager import DiskManager
from nexonara.storage.page import PAGE_SIZE, Page


def test_escribir_y_leer_pagina(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        page = Page.empty(0)
        rid = page.insert(b"hola")
        dm.write_page(page)

        assert page.dirty is False
        assert dm.page_count() == 1

        leida = dm.read_page(0)
        assert leida.page_id == 0
        assert leida.get(rid) == b"hola"
        assert leida.dirty is False


def test_allocate_page(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        p0 = dm.allocate_page()
        p1 = dm.allocate_page()

        assert (p0.page_id, p1.page_id) == (0, 1)
        assert dm.page_count() == 2
        assert len(dm.read_page(0).data) == PAGE_SIZE


def test_leer_pagina_inexistente(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        with pytest.raises(IndexError):
            dm.read_page(0)


def test_persistencia_entre_instancias(tmp_path) -> None:
    ruta = tmp_path / "prueba.db"

    with DiskManager(ruta) as dm:
        page = dm.allocate_page()
        page.insert(b"persistente")
        dm.write_page(page)

    with DiskManager(ruta) as dm:
        assert dm.read_page(0).get(0) == b"persistente"
