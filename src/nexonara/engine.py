"""Fachada principal del motor de base de datos."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType

from nexonara.catalog.catalog import Catalog
from nexonara.execution.executor import Executor, QueryResult
from nexonara.execution.planner import Planner
from nexonara.sql.parser import Parser


class Engine:
    """Coordina catálogo, parser, planificador, ejecutor, almacenamiento e índice AVL."""

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = str(data_dir)
        base_path = Path(data_dir)
        self.catalog = Catalog(base_path)
        self.planner = Planner(self.catalog)
        self.executor = Executor(self.catalog, base_path)

    def execute(self, query: str) -> QueryResult:
        """Ejecuta una consulta SQL de extremo a extremo."""
        statement = Parser(query).parse()
        plan = self.planner.plan(statement)
        return self.executor.execute(plan)

    def execute_script(self, script: str) -> list[QueryResult]:
        """Ejecuta múltiples sentencias SQL separadas por punto y coma."""
        results: list[QueryResult] = []
        for raw in script.split(";"):
            lines = [
                line for line in raw.splitlines() if not line.strip().startswith("--")
            ]
            stmt_text = "\n".join(lines).strip()
            if stmt_text:
                results.append(self.execute(stmt_text))
        return results

    def close(self) -> None:
        """Vuelca buffers y cierra los archivos de disco."""
        self.executor.close()

    def __enter__(self) -> Engine:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()