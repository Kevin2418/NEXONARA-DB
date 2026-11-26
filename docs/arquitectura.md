# Arquitectura de NEXONARA-DB

## Objetivo

Motor de base de datos relacional, didáctico, implementado en Python, con soporte para un subconjunto de SQL.

## Capas

1. **CLI (`cli.py`)**: REPL que recibe consultas y muestra resultados.
2. **Engine (`engine.py`)**: fachada que coordina todos los componentes.
3. **SQL (`sql/`)**: análisis léxico, sintáctico y AST.
4. **Catálogo (`catalog/`)**: metadatos de tablas, columnas y esquemas.
5. **Ejecución (`execution/`)**: planificación y ejecución de consultas.
6. **Almacenamiento (`storage/`)**: páginas, archivos y buffer pool.
7. **Tipos (`types/`)**: representación de valores y conversiones.

## Flujo de una consulta

```
texto SQL
  -> lexer
  -> parser
  -> AST
  -> planner
  -> executor
  -> storage / catalog
  -> resultado
```

## Formato de página

Cada página mide 4096 bytes y usa un directorio de slots:

```
+-------------+----------------------------+----------------------+
| slots (2 B) | directorio de slots (4 B)  | espacio libre        |
+-------------+----------------------------+----------------------+
                                                     ^
                                      los registros crecen desde
                                      el final hacia el inicio
```

- Cada entrada del directorio guarda el offset y la longitud de un registro.
- Longitud 0 significa slot libre o eliminado.
- El RID de un registro es el índice de su slot.
- La compactación recupera huecos sin cambiar los RID.

## Almacenamiento

- `DiskManager` traduce un `page_id` a la posición `page_id * 4096` del archivo.
- `BufferPool` mantiene páginas en memoria con política LRU.
- Una página fijada (pin) no puede expulsarse hasta llamar a `unpin_page`.
- Las páginas modificadas se marcan como sucias y se escriben al expulsarlas,
  al hacer `flush` o al cerrar el buffer.

## Componentes futuros

- `index/`: índice B+Tree para búsquedas eficientes.
- `transactions/`: WAL y control de transacciones.

## Decisiones iniciales

- Python 3.11 o superior.
- Sin dependencias externas en tiempo de ejecución.
- Páginas de 4096 bytes.
- Carpeta `data/` para los archivos de la base de datos (ignorada por Git).
