"""Script de carga de datasets de prueba (pequeño y mediano)."""

from __future__ import annotations

import argparse
from pathlib import Path

from nexonara.engine import Engine


def generate_medium_script(n: int = 2000) -> str:
    """Genera un script SQL mediano con n registros para probar AVL y paginación."""
    lines = [
        "CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, precio REAL, disponible BOOLEAN);"
    ]
    for i in range(1, n + 1):
        precio = round(10.0 + (i % 500) * 1.25, 2)
        disp = "true" if i % 4 != 0 else "false"
        lines.append(
            f"INSERT INTO productos VALUES ({i}, 'Producto_{i}', {precio}, {disp});"
        )
    return "\n".join(lines)


def load_dataset(dataset: str, data_dir: str = "data") -> int:
    """Carga el dataset 'small' o 'medium' en el motor y devuelve sentencias ejecutadas."""
    with Engine(data_dir) as db:
        if dataset == "small":
            sql_path = Path(__file__).resolve().parents[2] / "datasets" / "small.sql"
            script = sql_path.read_text(encoding="utf-8")
        elif dataset == "medium":
            script = generate_medium_script(2000)
        else:
            raise ValueError("Dataset inválido. Usa 'small' o 'medium'.")

        results = db.execute_script(script)
        return len(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datasets de prueba en NEXONARA-DB")
    parser.add_argument(
        "--dataset",
        choices=["small", "medium"],
        default="small",
        help="Tamaño del dataset a cargar (small o medium)",
    )
    parser.add_argument("--data-dir", default="data", help="Directorio de almacenamiento")
    args = parser.parse_args()

    total = load_dataset(args.dataset, args.data_dir)
    print(f"Dataset '{args.dataset}' cargado correctamente ({total} sentencias ejecutadas).")


if __name__ == "__main__":
    main()