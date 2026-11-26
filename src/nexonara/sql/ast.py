"""Nodos del árbol de sintaxis abstracta (AST) de las consultas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Statement:
    """Nodo base para cualquier sentencia SQL."""


# TODO: definir nodos para CREATE, INSERT, SELECT, UPDATE y DELETE.
