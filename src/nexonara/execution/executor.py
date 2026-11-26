"""Ejecutor de planes de consulta."""

from __future__ import annotations


class Executor:
    """Ejecuta un plan y produce resultados.

    TODO: recorrer operadores y devolver filas.
    """

    def execute(self, plan: object) -> list[tuple]:
        raise NotImplementedError
