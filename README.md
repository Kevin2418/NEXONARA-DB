# NEXONARA-DB

Proyecto final de Ciencias de la Computación I: motor de base de datos relacional implementado en Python desde cero, con almacenamiento paginado en disco e indexación mediante árbol autobalanceado **AVL**.

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

Iniciar la consola interactiva (REPL):

```powershell
python -m nexonara
```

Cargar datasets de prueba (pequeño y mediano):

```powershell
python -m nexonara.seed --dataset small
python -m nexonara.seed --dataset medium
```

## Pruebas

```powershell
python -m pytest
```

## Sintaxis SQL soportada (Ejemplos)

```sql
-- Gestión de esquemas
CREATE TABLE estudiantes (id INTEGER PRIMARY KEY, nombre TEXT, promedio REAL, activo BOOLEAN);
DROP TABLE estudiantes;

-- Inserción
INSERT INTO estudiantes VALUES (1, 'Ana', 4.5, true);

-- Consultas (por clave primaria, rango en índice AVL, igualdad/filtros y recorrido ordenado)
SELECT * FROM estudiantes;
SELECT * FROM estudiantes WHERE id = 1;
SELECT * FROM estudiantes WHERE id BETWEEN 1 AND 10;
SELECT * FROM estudiantes WHERE promedio >= 4.0;
SELECT * FROM estudiantes ORDER BY id ASC;

-- Actualización y eliminación
UPDATE estudiantes SET promedio = 4.8, activo = false WHERE id = 1;
DELETE FROM estudiantes WHERE id = 1;
```

## Estructura

```text
src/nexonara/
  catalog/      Metadatos de tablas, columnas y esquemas
  execution/    Planificador y ejecutor de consultas con atomicidad
  index/        Índice en árbol autobalanceado AVL (sin librerías externas)
  sql/          Lexer, parser y AST SQL propio
  storage/      Páginas de 4096 B con slots, DiskManager y BufferPool LRU
  types/        Tipos de datos (INTEGER, REAL, TEXT, BOOLEAN, NULL) y serialización
tests/          Pruebas automatizadas (CRUD, AVL, persistencia y recuperación)
docs/           Documentación técnica de alcance y arquitectura
datasets/       Datasets de prueba (pequeño y mediano)
data/           Archivos de la base de datos (ignorados por Git)
```

## Hoja de ruta

- [x] 1. Esqueleto del proyecto y REPL base.
- [x] 2. Gestión de almacenamiento, páginas con slots y BufferPool LRU.
- [ ] 3. Tipos de datos y catálogo persistente (`CREATE TABLE`, `DROP TABLE`).
- [ ] 4. Índice propio en árbol autobalanceado **AVL** ($O(\log n)$, rangos e *inorder*).
- [ ] 5. Parser SQL propio (lexer, parser y AST).
- [ ] 6. Operaciones CRUD (`INSERT`, `SELECT`, `UPDATE`, `DELETE`) y filtros `WHERE`.
- [ ] 7. Atomicidad básica y recuperación de estado e índice tras reinicio.
- [ ] 8. Datasets de prueba, suite completa de tests y guía de sustentación.