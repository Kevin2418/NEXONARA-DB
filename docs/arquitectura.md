# Arquitectura de NEXONARA-DB

## Objetivo

Motor de base de datos relacional, didáctico, implementado en Python, con soporte para un subconjunto de SQL.

## Capas

1. **CLI (`cli.py`)**: REPL que recibe consultas y muestra resultados.
2. **Engine (`engine.py`)**: fachada que coordina todos los componentes.
3. **SQL (`sql/`)**: análisis léxico, sintáctico y AST.
4. **Catálogo (`catalog/`)**: metadatos de tablas, columnas y esquemas.
5. **Ejecución (`execution/`)**: planificación y ejecución de consultas.
6. **Índices (`index/`)**: BST, AVL y rojo-negro en memoria; B+Tree persistente.
7. **Almacenamiento (`storage/`)**: páginas, archivos y buffer pool.
8. **Tipos (`types/`)**: representación de valores y conversiones.

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

## Índices

La interfaz `Index` asocia claves con RIDs (`page_id`, `slot_id`) y define
`insert`, `search`, `delete`, `range_scan`, `height` y `validate`.

- `BSTIndex`: árbol binario de búsqueda sin balanceo; sirve como línea base y
  se degenera con inserciones ordenadas.
- `AVLIndex`: mantiene la diferencia de altura entre subárboles como máximo 1.
  Prioriza búsquedas rápidas y usa rotaciones tras cada cambio.
- `RedBlackIndex`: mantiene altura negra uniforme y raíz negra. Es menos
  estricto que AVL y suele requerir menos rotaciones en inserciones y borrados.
- `BPlusTree`: pendiente; será el índice persistente sobre `Page` y
  `BufferPool`, con valores solo en las hojas y hojas enlazadas para rangos.

`validate()` comprueba las invariantes de cada árbol y se usa en las pruebas.

## Componentes futuros

- `index/bplustree.py`: índice persistente en disco.
- `transactions/`: WAL y control de transacciones.

## Decisiones iniciales

- Python 3.11 o superior.
- Sin dependencias externas en tiempo de ejecución.
- Páginas de 4096 bytes.
- Carpeta `data/` para los archivos de la base de datos (ignorada por Git).
