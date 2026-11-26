"""Fachada principal del motor de base de datos."""

from __future__ import annotations


class Engine:
    """Coordina los componentes del motor.

    TODO: conectar almacenamiento, catálogo, SQL y ejecución.
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = data_dir

    def execute(self, query: str) -> object:
        """Ejecuta una consulta SQL.

        TODO: delegar en lexer, parser, planner y executor.
        """
        raise NotImplementedError("El motor aún no está implementado.")
