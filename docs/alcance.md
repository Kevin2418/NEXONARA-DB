# Alcance del proyecto

## Incluido (MVP)

- Sentencias `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE` y `DELETE`.
- Tipos básicos: `INTEGER`, `TEXT`, `BOOLEAN` y `NULL`.
- Persistencia en archivos locales.
- Catálogo de tablas y columnas.
- Índices en memoria BST, AVL y rojo-negro.
- REPL para ejecutar consultas.

## Fases posteriores

- Índice B+Tree persistente.
- Filtros `WHERE` con comparaciones y `AND`/`OR`.
- `ORDER BY` y `LIMIT`.
- Transacciones y WAL.
- Recuperación tras fallos.

## Fuera de alcance

- SQL completo.
- Concurrencia multiusuario.
- Arquitectura cliente-servidor.
- JOINs complejos, subconsultas, triggers y vistas.

## Fases de desarrollo

1. ✅ Esqueleto del proyecto y REPL.
2. ✅ Almacenamiento y páginas.
3. ✅ Índices BST, AVL y rojo-negro.
4. Catálogo y `CREATE TABLE`.
5. B+Tree persistente.
6. `INSERT` y `SELECT` básicos.
7. Parser SQL propio.
8. `UPDATE`, `DELETE` y `WHERE`.
9. Transacciones.
