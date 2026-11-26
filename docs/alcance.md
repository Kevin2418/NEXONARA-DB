# Alcance del proyecto

## Incluido

- **Modelo relacional con esquema fijo** por tabla (`CREATE TABLE` y `DROP TABLE`).
- **Tipos de datos básicos:** `INTEGER`, `REAL`, `TEXT`, `BOOLEAN` y `NULL`.
- **Operaciones CRUD completas:** `INSERT`, `SELECT`, `UPDATE` y `DELETE`.
- **Consultas y filtros:** búsqueda exacta por clave primaria, búsqueda por rango (`BETWEEN` / `<, <=, >, >=`), filtros `WHERE` (`=`, `!=`, `<`, `<=`, `>`, `>=`, `AND`, `OR`) y recorrido ordenado (`ORDER BY` sobre el índice).
- **Índice propio en árbol AVL:** implementado desde cero sin librerías externas para la clave primaria (inserción, búsqueda, eliminación, rango y recorrido *inorder* en $O(\log n)$).
- **Persistencia y recuperación:** almacenamiento paginado binario en disco + metadatos persistentes que reconstruyen el índice AVL al reiniciar el motor.
- **Atomicidad básica:** reversión en memoria y descarga segura a disco para evitar corrupción o desincronización entre páginas e índice ante errores.
- **REPL interactivo** y script de carga de datasets de prueba (pequeño y mediano).

## Fuera de alcance

- SQL completo (subconsultas, vistas, triggers, procedimientos almacenados).
- Concurrencia multiusuario y bloqueo distribuido.
- `JOIN` complejos entre múltiples tablas.
- Arquitectura cliente-servidor en red.

## Fases de desarrollo

1. Esqueleto del proyecto y REPL base *(Completado)*.
2. Almacenamiento paginado, `DiskManager` y `BufferPool` LRU *(Completado)*.
3. Tipos de datos, serialización de tuplas y catálogo persistente.
4. Índice autobalanceado AVL y reconstrucción desde almacenamiento.
5. Lexer, Parser y AST para el subconjunto SQL.
6. Ejecutor CRUD, filtros `WHERE` y atomicidad básica.
7. Datasets de prueba, pruebas integrales y documentación técnica final.