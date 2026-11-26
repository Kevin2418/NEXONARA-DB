"""Interfaz de línea de comandos (REPL) del motor."""

from nexonara import __version__
from nexonara.engine import Engine
from nexonara.execution.executor import QueryResult


def _format_table(result: QueryResult) -> str:
    if not result.columns or result.rows is None:
        return result.message

    headers = result.columns
    str_rows = [[("NULL" if v is None else str(v)) for v in row] for row in result.rows]
    widths = [
        max([len(h)] + [len(r[i]) for r in str_rows])
        for i, h in enumerate(headers)
    ]

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    lines = [sep, header_line, sep]
    for r in str_rows:
        lines.append("| " + " | ".join(r[i].ljust(widths[i]) for i, _ in enumerate(headers)) + " |")
    lines.append(sep)
    lines.append(result.message)
    return "\n".join(lines)


def main() -> None:
    """Inicia el REPL de NEXONARA-DB."""
    print(f"NEXONARA-DB v{__version__} (Índice AVL + Almacenamiento Paginado)")
    print("Escribe 'salir' para terminar o 'tablas' para listar las tablas.")

    with Engine() as db:
        while True:
            try:
                consulta = input("nexonara> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not consulta:
                continue
            if consulta.lower() in {"salir", "exit", "quit"}:
                break
            if consulta.lower() in {"tablas", "tables"}:
                tablas = db.catalog.list_tables()
                print("Tablas:", ", ".join(tablas) if tablas else "(ninguna)")
                continue

            try:
                res = db.execute(consulta)
                print(_format_table(res))
            except Exception as exc:
                print(f"[ERROR] {exc}")