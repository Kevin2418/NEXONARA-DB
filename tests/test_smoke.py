"""Pruebas mínimas para validar la estructura inicial."""

import nexonara
from nexonara.engine import Engine


def test_version() -> None:
    assert nexonara.__version__ == "0.1.0"


def test_engine_instanciable() -> None:
    engine = Engine()
    assert engine.data_dir == "data"
