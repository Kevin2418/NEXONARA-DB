"""Pruebas del buffer pool."""

import pytest

from nexonara.storage.buffer_pool import BufferPool, BufferPoolFullError
from nexonara.storage.disk_manager import DiskManager


def test_pagina_fijada_no_se_expulsa(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        with BufferPool(dm, capacity=1) as pool:
            pool.new_page()

            with pytest.raises(BufferPoolFullError):
                pool.new_page()

            pool.unpin_page(0)
            page1 = pool.new_page()
            assert page1.page_id == 1
            assert pool.cached_pages == (1,)
            pool.unpin_page(1)


def test_recarga_desde_disco(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        with BufferPool(dm, capacity=1) as pool:
            page = pool.new_page()
            rid = page.insert(b"hola")
            assert pool.pin_count(0) == 1

            pool.unpin_page(0)
            assert pool.pin_count(0) == 0

            page1 = pool.new_page()  # expulsa la página 0, que estaba sucia
            assert page1.page_id == 1
            pool.unpin_page(1)

            recargada = pool.get_page(0)
            assert recargada.get(rid) == b"hola"
            pool.unpin_page(0)


def test_flush_page(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        with BufferPool(dm, capacity=2) as pool:
            page = pool.new_page()
            page.insert(b"datos")
            assert page.dirty is True

            pool.flush_page(0)

            assert page.dirty is False
            assert dm.read_page(0).get(0) == b"datos"
            pool.unpin_page(0)


def test_get_page_comparte_instancia(tmp_path) -> None:
    with DiskManager(tmp_path / "prueba.db") as dm:
        with BufferPool(dm, capacity=2) as pool:
            page = pool.new_page()
            pool.unpin_page(0)

            assert pool.get_page(0) is page
            assert pool.pin_count(0) == 1
            pool.unpin_page(0)
