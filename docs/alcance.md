# Alcance del proyecto

## Incluido (MVP)

- Sentencias `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE` y `DELETE`.
- Tipos básicos: `INTEGER`, `TEXT`, `BOOLEAN` y `NULL`.
- Persistencia en archivos locales.
- Catálogo de tablas y columnas.
- REPL para ejecutar consultas.

## Fases posteriores

- Índices B+Tree.
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

1. Esqueleto del proyecto y REPL.
2. Almacenamiento y páginas.
3. Catálogo y `CREATE TABLE`.
4. `INSERT` y `SELECT` básicos.
5. Parser SQL propio.
6. `UPDATE`, `DELETE` y `WHERE`.
7. Índices.
8. Transacciones.
