# NEXONARA-DB

Proyecto final de Ciencias de la Computación I: motor de base de datos implementado en Python.

## Requisitos

- Python 3.11 o superior

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` instala el proyecto en modo editable junto con `pytest`.

## Uso

El REPL todavía es un esqueleto:

```powershell
python -m nexonara
```

Para ver el almacenamiento y los índices funcionando juntos:

```powershell
python examples/demo.py
```

## Pruebas

```powershell
python -m pytest
```

## Benchmark de índices

```powershell
python benchmarks/compare_indexes.py
```

Compara BST, AVL y rojo-negro con datos aleatorios y ordenados.

## Estructura

```
src/nexonara/   Código del motor
  index/        BST, AVL y rojo-negro
tests/          Pruebas automatizadas
benchmarks/     Comparación de índices
examples/       Demos ejecutables
docs/           Documentación de arquitectura y alcance
data/           Archivos de la base de datos (ignorados por Git)
```

## Hoja de ruta

1. Esqueleto del proyecto y REPL.
2. Gestión de almacenamiento y páginas.
3. Índices BST, AVL y rojo-negro.
4. Catálogo de tablas.
5. B+Tree persistente.
6. Operaciones INSERT y SELECT.
7. Parser SQL propio.
8. UPDATE, DELETE y filtros.
9. Transacciones y recuperación.
