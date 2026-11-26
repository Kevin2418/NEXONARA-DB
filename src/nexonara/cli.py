"""Interfaz de línea de comandos (REPL) del motor."""

from nexonara import __version__


def main() -> None:
    """Inicia el REPL de NEXONARA-DB."""
    print(f"NEXONARA-DB v{__version__}")
    print("Escribe 'salir' para terminar.")

    while True:
        try:
            consulta = input("nexonara> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if consulta.lower() in {"salir", "exit", "quit"}:
            break
        if consulta:
            print("Aún no implementado.")
