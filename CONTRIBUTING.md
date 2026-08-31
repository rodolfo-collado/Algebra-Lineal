# Guía de contribución

## Flujo de ramas

```text
main
 ↑
develop
 ↑
feature/*
```

- `main` recibe únicamente versiones presentables. No se trabaja directamente sobre
  ella.
- `develop` es la rama de integración y el punto de partida de todo el desarrollo.
- Cada cambio relevante se hace en una rama `feature/*` creada desde `develop`.

Crear una rama de trabajo:

```bash
git checkout develop
git pull
git checkout -b feature/nombre-descriptivo
```

## Pull requests

- Las ramas `feature/*` se integran a `develop` mediante pull request.
- No es obligatorio esperar la aprobación de otro colaborador.
- Si el PR está limpio, sin conflictos y las verificaciones pasan, el propio
  colaborador puede hacer merge.
- Después del merge, elimina la rama feature local y remota.

## Commits

Se usan [Conventional Commits](https://www.conventionalcommits.org/):

```text
<tipo>: <descripción en minúsculas>
```

Tipos habituales: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`.

Ejemplos:

```text
feat: agregar resolucion por gauss
fix: corregir indice fuera de rango al modificar elementos
test: cubrir sistemas inconsistentes
```

Mantén los commits razonablemente pequeños y descriptivos. Separa los cambios
cuando tengan propósitos distintos.

## Antes de abrir un PR

Ejecuta las pruebas desde la raíz del repositorio:

```bash
python -m unittest discover -v
```

Comprueba también que la aplicación siga iniciando:

```bash
python main.py
```

## Restricciones matemáticas

Este es un proyecto educativo: **los algoritmos de álgebra lineal deben
implementarse manualmente**.

Está prohibido utilizar:

- NumPy;
- SciPy;
- SymPy para resolver operaciones de álgebra lineal;
- funciones de librerías externas que calculen directamente Gauss, Gauss-Jordan,
  rango, determinantes, sistemas de ecuaciones u operaciones equivalentes;
- cualquier librería que sustituya el desarrollo manual del algoritmo.

La implementación debe construirse con herramientas estándar de Python: listas,
listas anidadas, `if` / `else`, `for`, `while`, funciones, operaciones aritméticas
y estructuras propias del lenguaje.

`fractions.Fraction` sí está permitido: pertenece a la biblioteca estándar y
únicamente representa números racionales con exactitud, no resuelve ningún
algoritmo por sí mismo.

No agregues NumPy, SciPy, SymPy ni equivalentes a las dependencias del proyecto.

## Comentarios en el código

Comenta solo cuando ayude a entender una decisión que no es evidente. Prefiere
comentarios de una línea, breves, que expliquen el porqué.

Evita comentarios que repiten lo que el código ya dice:

```python
# Recorre cada fila
for fila in matriz:
```

Un comentario útil se ve así:

```python
# La ultima columna representa los terminos independientes.
```

No agregues docstrings largos solo por decorar.

## Configuración local

Las configuraciones de editores (`.idea/`) y de asistentes de IA (`CLAUDE.md`,
`.claude/`, `AGENTS.md`, `.cursor/`, entre otros) están en `.gitignore` y no se
versionan. La documentación compartida del proyecto vive en `README.md` y en este
archivo.
