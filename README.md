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

```powershell
python -m nexonara
```

## Pruebas

```powershell
python -m pytest
```

## Estructura

```
src/nexonara/   Código del motor
tests/          Pruebas automatizadas
docs/           Documentación de arquitectura y alcance
data/           Archivos de la base de datos (ignorados por Git)
```

## Hoja de ruta

1. Esqueleto del proyecto y REPL.
2. Gestión de almacenamiento y páginas.
3. Catálogo de tablas.
4. Operaciones INSERT y SELECT.
5. Parser SQL propio.
6. UPDATE, DELETE y filtros.
7. Índices B+Tree.
8. Transacciones y recuperación.
