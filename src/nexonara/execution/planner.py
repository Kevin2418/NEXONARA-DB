"""Planificador: transforma un AST en un plan de ejecución."""

from __future__ import annotations

from nexonara.sql.ast import Statement


class Planner:
    """Genera un plan a partir de una sentencia.

    TODO: definir operadores como scan, insert y filter.
    """

    def plan(self, statement: Statement) -> object:
        raise NotImplementedError
