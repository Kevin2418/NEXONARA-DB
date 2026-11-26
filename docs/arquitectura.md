# Arquitectura de NEXONARA-DB

## Objetivo

Motor de base de datos relacional implementado en Python desde cero, con almacenamiento paginado en disco e indexación en memoria mediante árbol autobalanceado **AVL**, manejado a través de una interfaz CLI/REPL.

## Capas del sistema

1. **CLI (`cli.py`)**: REPL interactivo que lee sentencias SQL, muestra resultados tabulares y reporta errores sin cerrar el motor.
2. **Engine (`engine.py`)**: fachada principal que inicializa disco, catálogo e índices y coordina la ejecución atómica de cada consulta.
3. **SQL (`sql/`)**: análisis léxico (`lexer.py`), sintáctico (`parser.py`) y árbol de sintaxis abstracta (`ast.py`).
4. **Catálogo (`catalog/`)**: definición y persistencia en JSON de esquemas de tablas, columnas, tipos y clave primaria.
5. **Índice (`index/avl.py`)**: árbol autobalanceado **AVL** implementado desde cero que mapea `clave_primaria -> (page_id, slot_id)` para acceso en $O(\log n)$, búsquedas por rango y recorrido *inorder*.
6. **Ejecución (`execution/`)**: planificación (`planner.py`, elige búsqueda por índice AVL vs. escaneo secuencial) y ejecución (`executor.py`).
7. **Almacenamiento (`storage/`)**: páginas de 4096 bytes con directorio de slots (`page.py`), gestor de archivos (`disk_manager.py`) y caché LRU (`buffer_pool.py`).
8. **Tipos (`types/`)**: validación, conversión y serialización binaria de celdas (`INTEGER`, `REAL`, `TEXT`, `BOOLEAN`, `NULL`).

## Flujo de una consulta

    texto SQL
      -> Lexer (tokens)
      -> Parser (AST)
      -> Planner (usa índice AVL si filtra por PK, o TableScan)
      -> Executor (validación de esquema + atomicidad)
      -> Index (AVL) + BufferPool / DiskManager / Catalog
      -> Resultado / Flush a disco

## Formato de página (4096 bytes)

    +-------------+----------------------------+----------------------+
    | slots (2 B) | directorio de slots (4 B)  | espacio libre        |
    +-------------+----------------------------+----------------------+
                                                         ^
                                          los registros crecen desde
                                          el final hacia el inicio

- Cada entrada del directorio guarda `(offset, length)` de un registro serializado.
- `length == 0` indica un slot libre o eliminado.
- El **RID** de un registro es el par `(page_id, slot_id)`. Los `slot_id` no cambian al compactar la página, manteniendo estables las referencias guardadas en el índice AVL.

## Persistencia, recuperación y atomicidad

- **Datos de filas:** se almacenan en archivos binarios por tabla (`data/<table>.db`) gestionados por `DiskManager` y `BufferPool` (páginas de 4096 bytes).
- **Metadatos del catálogo:** se guardan de forma atómica en `data/catalog.json` (escritura a archivo temporal + `os.replace`).
- **Recuperación al reiniciar:** al iniciar `Engine`, se lee `catalog.json`, se recorren las páginas activas de cada tabla en disco y se reconstruye automáticamente su árbol **AVL** en memoria.
- **Atomicidad:** si una operación (`INSERT`, `UPDATE`, `DELETE`) falla por validación, clave duplicada o error de ejecución, se revierte el estado en memoria antes de volcar cambios (`flush_all`) a disco.