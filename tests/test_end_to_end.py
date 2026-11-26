"""Pruebas integrales de NEXONARA-DB: CRUD, índice AVL, atomicidad y persistencia."""

from pathlib import Path

import pytest

from nexonara.engine import Engine
from nexonara.seed import load_dataset


def test_crud_range_and_filters(tmp_path: Path) -> None:
    with Engine(str(tmp_path)) as db:
        db.execute(
            "CREATE TABLE estudiantes (id INTEGER PRIMARY KEY, nombre TEXT, promedio REAL, activo BOOLEAN);"
        )
        db.execute("INSERT INTO estudiantes VALUES (10, 'Ana', 4.5, true);")
        db.execute("INSERT INTO estudiantes VALUES (5, 'Luis', 3.2, false);")
        db.execute("INSERT INTO estudiantes VALUES (20, 'Carla', 4.9, true);")
        db.execute("INSERT INTO estudiantes VALUES (15, 'Diego', 3.8, true);")

        # Búsqueda exacta por PK (usa índice AVL)
        res_pk = db.execute("SELECT * FROM estudiantes WHERE id = 15;")
        assert res_pk.rows == [[15, "Diego", 3.8, True]]

        # Búsqueda por rango en índice AVL (devuelve ordenado por PK)
        res_range = db.execute("SELECT id, nombre FROM estudiantes WHERE id BETWEEN 6 AND 20;")
        assert res_range.rows == [[10, "Ana"], [15, "Diego"], [20, "Carla"]]

        # Filtro compuesto AND / OR
        res_filter = db.execute(
            "SELECT nombre FROM estudiantes WHERE promedio >= 4.0 AND activo = true ORDER BY id DESC;"
        )
        assert res_filter.rows == [["Carla"], ["Ana"]]

        # UPDATE y DELETE
        db.execute("UPDATE estudiantes SET promedio = 4.1 WHERE id = 5;")
        assert db.execute("SELECT promedio FROM estudiantes WHERE id = 5;").rows == [[4.1]]

        db.execute("DELETE FROM estudiantes WHERE id = 10;")
        assert db.execute("SELECT * FROM estudiantes WHERE id = 10;").rows == []


def test_atomicity_on_duplicate_or_type_error(tmp_path: Path) -> None:
    with Engine(str(tmp_path)) as db:
        db.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, precio REAL);")
        db.execute("INSERT INTO items VALUES (1, 10.5);")

        # Clave duplicada no corrompe ni altera el estado
        with pytest.raises(ValueError, match="duplicada"):
            db.execute("INSERT INTO items VALUES (1, 99.9);")

        # Tipo inválido no corrompe
        with pytest.raises(TypeError):
            db.execute("INSERT INTO items VALUES (2, 'no_es_numero');")

        assert db.execute("SELECT * FROM items;").rows == [[1, 10.5]]


def test_persistence_and_avl_recovery_after_restart(tmp_path: Path) -> None:
    # Sesión 1: crear, insertar y cerrar
    with Engine(str(tmp_path)) as db1:
        db1.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT);")
        for i in range(1, 31):
            db1.execute(f"INSERT INTO usuarios VALUES ({i}, 'User_{i}');")
        db1.execute("DELETE FROM usuarios WHERE id = 15;")

    # Sesión 2: reabrir desde disco y verificar que el árbol AVL se reconstruyó
    with Engine(str(tmp_path)) as db2:
        rt = db2.executor._runtime("usuarios")
        assert len(rt.index) == 29
        assert rt.index.is_balanced()
        assert db2.execute("SELECT * FROM usuarios WHERE id = 15;").rows == []
        assert db2.execute("SELECT * FROM usuarios WHERE id = 22;").rows == [[22, "User_22"]]


def test_seed_datasets(tmp_path: Path) -> None:
    count_small = load_dataset("small", str(tmp_path / "small_db"))
    assert count_small == 16  # 1 CREATE + 15 INSERT

    count_med = load_dataset("medium", str(tmp_path / "med_db"))
    assert count_med == 2001  # 1 CREATE + 2000 INSERT

    with Engine(str(tmp_path / "med_db")) as db:
        rt = db.executor._runtime("productos")
        assert len(rt.index) == 2000
        assert rt.index.is_balanced()
        assert db.execute("SELECT id, nombre FROM productos WHERE id = 1999;").rows == [
            [1999, "Producto_1999"]
        ]