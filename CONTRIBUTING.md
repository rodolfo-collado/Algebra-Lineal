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

## Entorno de trabajo

El proyecto se gestiona con [uv](https://docs.astral.sh/uv/). Después de clonar,
desde la raíz del repositorio:

```bash
uv sync
```

Eso crea `.venv/` con las versiones exactas de `uv.lock`. Para ejecutar cualquier
cosa dentro de ese entorno usa `uv run`:

```bash
uv run python main.py
```

## Dependencias

Las dependencias directas del proyecto se declaran en `pyproject.toml`. Lista ahí
únicamente lo que el proyecto importa de forma directa, no dependencias
transitivas. `uv.lock` guarda las versiones exactas resueltas a partir de esa
declaración, y también se versiona.

Cualquier cambio de dependencia se hace con uv, no editando los archivos a mano:

```bash
uv add <dependencia>
uv remove <dependencia>
```

- `pyproject.toml` y `uv.lock` se actualizan y se commitean juntos. `uv add` y
  `uv remove` ya modifican los dos.
- Nunca edites `uv.lock` a mano. Si quedó desincronizado, regenéralo con `uv lock`.
- No uses `uv pip install` ni `pip install` para las dependencias del proyecto:
  no quedan declaradas y el lockfile deja de reflejar la realidad.

## Antes de abrir un PR

Desde la raíz del repositorio, ejecuta las mismas verificaciones que corre el CI:

```bash
uv lock --check
uv run python -m unittest discover -v
uv run python -m compileall -q backend frontend tests main.py manage.py desktop.py
```

Comprueba también que la aplicación siga iniciando:

```bash
uv run python main.py
```

La interfaz desktop durante desarrollo se puede iniciar con:

```bash
uv run python desktop.py
```

Para generar la distribución de Windows, usa la configuración versionada de
PyInstaller desde la raíz del proyecto:

```bash
uv run pyinstaller --noconfirm --clean AlgebraLineal.spec
```

## Integración continua

`.github/workflows/ci.yml` ejecuta esas mismas verificaciones en cada pull request
hacia `develop` o `main`, y en cada push a esas ramas.

**Un PR no se fusiona si el CI está en rojo.** Si un check falla, corrígelo en la
misma rama `feature/*` y espera una ejecución verde. No desactives un check para
poder mergear.

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

`colorama` también está permitido, pero únicamente para dar color a la terminal:
no participa en ningún cálculo ni sustituye ningún algoritmo.

No agregues NumPy, SciPy, SymPy ni equivalentes a las dependencias del proyecto.

`tests/test_restricciones_proyecto.py` comprueba esta regla automáticamente, tanto
en local como en el CI: analiza con `ast` los imports de `backend/`, `frontend/`,
`tests/` y `main.py`, y lee las dependencias declaradas en `pyproject.toml` con
`tomllib`. Si aparece una librería prohibida, la prueba falla indicando cuál es.

La prohibición se limita a librerías que sustituyan el trabajo matemático manual.
Las dependencias de interfaz o infraestructura, como `colorama`, siguen siendo
perfectamente válidas.

## Matrices y sistemas de ecuaciones

Son dos conceptos distintos y el código debe mantenerlos separados:

- Gauss-Jordan se aplica a **cualquier matriz rectangular**. No se rechaza una
  matriz por no ser cuadrada ni por no tener la forma `n x (n+1)`.
- El significado de una matriz **no se deduce de sus dimensiones**. Una matriz
  `3 x 3` puede ser una matriz cualquiera o el sistema de 3 ecuaciones y 2
  variables.
- Cuando una matriz representa un sistema, quien llama lo indica de forma
  explícita usando `resolver_sistema_gauss` o `resolver_sistema_gauss_jordan`, y
  la última columna son los términos independientes.
- Antes de resolver, la comprobación se hace con `validar_matriz_aumentada`, no
  comparando `filas` con `columnas`.

Al escribir el algoritmo, no asumas que toda columna tendrá pivote, que toda fila
tendrá pivote ni que la matriz terminará como la identidad.

## Gauss y Gauss-Jordan

Son dos operaciones distintas que comparten piezas:

- `backend/operaciones_filas.py` tiene las operaciones elementales (buscar
  pivote, intercambiar, normalizar, eliminar) y el registro de pasos.
- `backend/gauss.py` solo elimina **hacia abajo** y deja la forma escalonada.
- `backend/gauss_jordan.py` parte de `aplicar_gauss` y solo añade la eliminación
  **hacia arriba**.

No dupliques el escalonamiento para implementar un método nuevo, y no añadas otra
capa si las utilidades actuales se pueden reutilizar tal cual.

Los dos métodos deben coincidir siempre en la clasificación y en la solución
final. Pueden diferir en los pasos, en la matriz resultante y en el sistema
resultante, porque uno llega a la forma escalonada y el otro a la reducida. Las
pruebas comparan resultados, nunca pasos.

Las clasificaciones visibles son exactamente estas tres:

```text
Consistente de solución única
Consistente de soluciones infinitas
Inconsistente
```

No se muestran rangos al usuario.

## La interpretación del resultado vive en el backend

Traducir una matriz resuelta a su sistema de ecuaciones, detectar las variables
libres y despejar el conjunto solución son operaciones matemáticas, no de
presentación. Van en `backend/` y deben poder reutilizarse desde cualquier
frontend. Reglas:

- `backend/sistemas.py` devuelve el sistema resultante y la solución ya listos
  para mostrarse; el frontend solo les pone título y color;
- ninguna de esas cadenas puede llevar códigos ANSI, títulos ni nada específico
  de la terminal: `x1 = 1 + 5x3`, `x3 es libre` o `0 = 3` sirven igual en HTML;
- las expresiones lineales se construyen con `backend/expresiones.py`, calculando
  con `Fraction` y formateando solo al final. No se despeja concatenando texto;
- Gauss y Gauss-Jordan comparten esa interpretación. No dupliques la lectura del
  resultado por método;
- una columna sin pivote produce una variable libre; una fila `0 = k` con `k`
  distinto de cero produce un sistema inconsistente. Son casos distintos, y en el
  segundo no se declara ninguna variable libre.

## El parser no depende del frontend

`backend/parser_sistemas.py` convierte texto en una matriz aumentada y es la
única puerta de entrada de los sistemas escritos a mano. Reglas:

- no puede usar `input()`, `print()`, `colorama` ni nada de `frontend/`;
- recibe texto y devuelve una matriz, o lanza `ValueError` con un mensaje
  entendible;
- el frontend atrapa ese `ValueError` y lo muestra con las utilidades de consola;
- la interpretación se hace con `re`, nunca con `eval`, `exec` ni librerías
  algebraicas externas.

La conversión de texto a número está centralizada en `convertir_a_numero`. Si hace
falta leer un número en otro sitio, reutilízala en vez de escribir otro parser.

El parser devuelve solo la matriz aumentada, sin metadata sobre su origen: el
backend matemático no debe saber si el sistema se escribió como texto o se ingresó
coeficiente por coeficiente.

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

## Herramientas que podríamos añadir más adelante

El proyecto todavía no usa linters ni formateadores, a propósito: por ahora las
verificaciones son pruebas y compilación. Si en algún momento hace falta, serían
candidatos razonables, en este orden:

- un formateador y linter (por ejemplo Ruff) para unificar estilo;
- cobertura de pruebas en el CI;
- `pre-commit` para correr las verificaciones antes de cada commit.

Ninguno es un requisito actual. Si se añade alguno, debe entrar como cambio propio
y no colado dentro de otra tarea.
