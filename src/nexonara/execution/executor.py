"""Ejecutor de planes de consulta sobre páginas, BufferPool e índice AVL."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nexonara.catalog.catalog import Catalog, Column, TableSchema
from nexonara.execution.planner import Plan
from nexonara.index.avl import AVLTree
from nexonara.sql.ast import (
    BetweenExpr,
    ComparisonExpr,
    CreateTableStmt,
    DeleteStmt,
    DropTableStmt,
    Expr,
    InsertStmt,
    LogicalExpr,
    SelectStmt,
    UpdateStmt,
)
from nexonara.storage.buffer_pool import BufferPool
from nexonara.storage.disk_manager import DiskManager
from nexonara.types.values import cast_value, deserialize_row, serialize_row


@dataclass
class QueryResult:
    """Resultado uniforme de una ejecución SQL."""

    message: str
    columns: list[str] | None = None
    rows: list[list[Any]] | None = None


class TableRuntime:
    """Mantiene abiertos el BufferPool y el índice AVL de una tabla."""

    def __init__(self, schema: TableSchema, db_path: Path) -> None:
        self.schema = schema
        self.db_path = db_path
        self.disk = DiskManager(db_path)
        self.pool = BufferPool(self.disk, capacity=64)
        self.index = AVLTree()
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """Reconstruye el índice AVL recorriendo todas las páginas activas en disco."""
        self.index.clear()
        pk_idx = self.schema.pk_index
        total_pages = self.disk.page_count()
        for page_id in range(total_pages):
            page = self.pool.get_page(page_id)
            try:
                for slot_id in range(page.slot_count):
                    try:
                        payload = page.get(slot_id)
                    except KeyError:
                        continue  # Slot eliminado
                    row = deserialize_row(payload)
                    self.index.insert(row[pk_idx], (page_id, slot_id))
            finally:
                self.pool.unpin_page(page_id)

    def insert_row_to_page(self, payload: bytes) -> tuple[int, int]:
        """Inserta bytes en la última página con espacio o asigna una nueva."""
        total_pages = self.disk.page_count()
        if total_pages > 0:
            last_id = total_pages - 1
            page = self.pool.get_page(last_id)
            try:
                slot_id = page.insert(payload)
                return (last_id, slot_id)
            except Exception:
                pass
            finally:
                self.pool.unpin_page(last_id)

        new_page = self.pool.new_page()
        new_id = new_page.page_id
        try:
            slot_id = new_page.insert(payload)
            return (new_id, slot_id)
        finally:
            self.pool.unpin_page(new_id)

    def read_rid(self, rid: tuple[int, int]) -> list[Any]:
        page_id, slot_id = rid
        page = self.pool.get_page(page_id)
        try:
            return deserialize_row(page.get(slot_id))
        finally:
            self.pool.unpin_page(page_id)

    def delete_rid(self, rid: tuple[int, int]) -> None:
        page_id, slot_id = rid
        page = self.pool.get_page(page_id)
        try:
            page.delete(slot_id)
        finally:
            self.pool.unpin_page(page_id)

    def close(self) -> None:
        self.pool.close()


class Executor:
    """Ejecuta planes SQL con sincronización AVL y atomicidad básica."""

    def __init__(self, catalog: Catalog, data_dir: str | Path = "data") -> None:
        self.catalog = catalog
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._runtimes: dict[str, TableRuntime] = {}
        for table_name in self.catalog.list_tables():
            schema = self.catalog.get_table(table_name)
            self._runtimes[table_name.lower()] = TableRuntime(
                schema, self._table_file(schema.name)
            )

    def _table_file(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name.lower()}.db"

    def _runtime(self, table_name: str) -> TableRuntime:
        key = table_name.lower()
        if key not in self._runtimes:
            schema = self.catalog.get_table(table_name)
            self._runtimes[key] = TableRuntime(schema, self._table_file(schema.name))
        return self._runtimes[key]

    def close(self) -> None:
        for rt in self._runtimes.values():
            rt.close()
        self._runtimes.clear()

    def execute(self, plan: Plan) -> QueryResult:
        stmt = plan.statement

        if isinstance(stmt, CreateTableStmt):
            cols = [
                Column(name=c.name, type_name=c.type_name, primary_key=c.primary_key)
                for c in stmt.columns
            ]
            schema = TableSchema(name=stmt.table_name, columns=cols)
            self.catalog.create_table(schema)
            rt = TableRuntime(schema, self._table_file(schema.name))
            rt.pool.flush_all()
            self._runtimes[schema.name.lower()] = rt
            return QueryResult(message=f"Tabla '{schema.name}' creada.")

        if isinstance(stmt, DropTableStmt):
            schema = self.catalog.drop_table(stmt.table_name)
            key = schema.name.lower()
            rt = self._runtimes.pop(key, None)
            if rt is not None:
                rt.close()
            db_file = self._table_file(schema.name)
            if db_file.exists():
                db_file.unlink()
            return QueryResult(message=f"Tabla '{schema.name}' eliminada.")

        if isinstance(stmt, InsertStmt):
            return self._exec_insert(stmt)

        if isinstance(stmt, SelectStmt):
            return self._exec_select(plan, stmt)

        if isinstance(stmt, UpdateStmt):
            return self._exec_update(plan, stmt)

        if isinstance(stmt, DeleteStmt):
            return self._exec_delete(plan, stmt)

        raise ValueError(f"Plan no soportado: {type(stmt).__name__}")

    def _exec_insert(self, stmt: InsertStmt) -> QueryResult:
        rt = self._runtime(stmt.table_name)
        clean_row = rt.schema.validate_row(stmt.values)
        pk_val = clean_row[rt.schema.pk_index]

        if rt.index.search(pk_val) is not None:
            raise ValueError(f"Clave primaria duplicada: {pk_val!r}")

        backup_index = copy.deepcopy(rt.index)
        try:
            payload = serialize_row(clean_row)
            rid = rt.insert_row_to_page(payload)
            rt.index.insert(pk_val, rid)
            rt.pool.flush_all()
            return QueryResult(message="1 fila insertada.")
        except Exception:
            rt.index = backup_index
            raise

    def _candidate_rids(self, plan: Plan, rt: TableRuntime) -> list[tuple[Any, tuple[int, int]]]:
        pk_type = rt.schema.pk_column.type_name
        if plan.access_method == "AVL_PK":
            key = cast_value(plan.index_key, pk_type)
            rid = rt.index.search(key)
            return [(key, rid)] if rid is not None else []

        if plan.access_method == "AVL_RANGE":
            low = cast_value(plan.range_low, pk_type) if plan.range_low is not None else None
            high = cast_value(plan.range_high, pk_type) if plan.range_high is not None else None
            return rt.index.range_query(low, high)

        # SEQ_SCAN: recorre en orden del índice AVL
        return rt.index.inorder()

    def _exec_select(self, plan: Plan, stmt: SelectStmt) -> QueryResult:
        rt = self._runtime(stmt.table_name)
        candidates = self._candidate_rids(plan, rt)

        matched_rows: list[list[Any]] = []
        for _, rid in candidates:
            row = rt.read_rid(rid)
            if stmt.where is None or self._eval_where(stmt.where, rt.schema, row):
                matched_rows.append(row)

        if stmt.order_by is not None:
            col_idx = rt.schema.column_index(stmt.order_by)
            matched_rows.sort(
                key=lambda r: (r[col_idx] is None, r[col_idx]),
                reverse=stmt.order_desc,
            )

        if stmt.columns is None:
            out_cols = [c.name for c in rt.schema.columns]
            out_rows = matched_rows
        else:
            col_indices = [rt.schema.column_index(c) for c in stmt.columns]
            out_cols = [rt.schema.columns[i].name for i in col_indices]
            out_rows = [[r[i] for i in col_indices] for r in matched_rows]

        return QueryResult(
            message=f"{len(out_rows)} fila(s) encontrada(s).",
            columns=out_cols,
            rows=out_rows,
        )

    def _exec_update(self, plan: Plan, stmt: UpdateStmt) -> QueryResult:
        rt = self._runtime(stmt.table_name)
        pk_idx = rt.schema.pk_index
        pk_name = rt.schema.pk_column.name.lower()

        # Validar columnas antes de tocar datos (atomicidad)
        updates_by_idx: dict[int, Any] = {}
        for col_name, raw_val in stmt.assignments.items():
            if col_name.lower() == pk_name:
                raise ValueError("No se permite modificar la clave primaria en UPDATE")
            idx = rt.schema.column_index(col_name)
            updates_by_idx[idx] = cast_value(raw_val, rt.schema.columns[idx].type_name)

        candidates = self._candidate_rids(plan, rt)
        targets: list[tuple[Any, tuple[int, int], list[Any]]] = []
        for pk_val, rid in candidates:
            row = rt.read_rid(rid)
            if stmt.where is None or self._eval_where(stmt.where, rt.schema, row):
                new_row = list(row)
                for idx, val in updates_by_idx.items():
                    new_row[idx] = val
                rt.schema.validate_row(new_row)
                targets.append((pk_val, rid, new_row))

        backup_index = copy.deepcopy(rt.index)
        try:
            for pk_val, old_rid, new_row in targets:
                new_payload = serialize_row(new_row)
                rt.delete_rid(old_rid)
                new_rid = rt.insert_row_to_page(new_payload)
                rt.index.update(pk_val, new_rid)
            rt.pool.flush_all()
            return QueryResult(message=f"{len(targets)} fila(s) actualizada(s).")
        except Exception:
            rt.index = backup_index
            raise

    def _exec_delete(self, plan: Plan, stmt: DeleteStmt) -> QueryResult:
        rt = self._runtime(stmt.table_name)
        candidates = self._candidate_rids(plan, rt)

        targets: list[tuple[Any, tuple[int, int]]] = []
        for pk_val, rid in candidates:
            row = rt.read_rid(rid)
            if stmt.where is None or self._eval_where(stmt.where, rt.schema, row):
                targets.append((pk_val, rid))

        backup_index = copy.deepcopy(rt.index)
        try:
            for pk_val, rid in targets:
                rt.delete_rid(rid)
                rt.index.delete(pk_val)
            rt.pool.flush_all()
            return QueryResult(message=f"{len(targets)} fila(s) eliminada(s).")
        except Exception:
            rt.index = backup_index
            raise

    def _eval_where(self, expr: Expr, schema: TableSchema, row: list[Any]) -> bool:
        if isinstance(expr, LogicalExpr):
            if expr.op == "AND":
                return self._eval_where(expr.left, schema, row) and self._eval_where(
                    expr.right, schema, row
                )
            return self._eval_where(expr.left, schema, row) or self._eval_where(
                expr.right, schema, row
            )

        if isinstance(expr, BetweenExpr):
            idx = schema.column_index(expr.column)
            val = row[idx]
            if val is None:
                return False
            t = schema.columns[idx].type_name
            low = cast_value(expr.low, t)
            high = cast_value(expr.high, t)
            return low <= val <= high

        if isinstance(expr, ComparisonExpr):
            idx = schema.column_index(expr.column)
            val = row[idx]
            t = schema.columns[idx].type_name
            target = cast_value(expr.value, t)

            if expr.op == "=":
                return val == target
            if expr.op == "!=":
                return val != target
            if val is None or target is None:
                return False
            if expr.op == "<":
                return val < target
            if expr.op == "<=":
                return val <= target
            if expr.op == ">":
                return val > target
            if expr.op == ">=":
                return val >= target

        raise ValueError(f"Expresión WHERE inválida: {expr}")