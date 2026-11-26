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
- Después del merge, comprueba que la rama esté completamente integrada antes
  de limpiarla. Usa `git branch -d` para la local; la remota se elimina solo
  como una acción explícita de mantenimiento.

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

El [índice de documentación](docs/README.md) reúne las guías de uso, aprendizaje,
mantenimiento e historial. Para contribuir, empieza en [Desarrollo](docs/desarrollo.md)
con `uv sync --locked`. La [guía de ejecución](docs/ejecucion.md) detalla los
puntos de entrada para consola, Django y escritorio.

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

Ejecuta las [verificaciones de Pruebas](docs/pruebas.md): lockfile, suite,
Django, compilación y `git diff --check`. Si editas documentación, ejecuta
`uv run --locked python -m unittest tests.test_documentacion` y revisa cómo
GitHub muestra los enlaces, las imágenes y los bloques de código. Si cambias el
empaquetado, realiza también
el [build y smoke Windows](docs/instalacion-windows.md).

Si cambias un flujo interactivo, ejecuta también sus
[pruebas de navegador](docs/pruebas.md). Comprueba el manejo con teclado y el
flujo básico sin JavaScript. Para cambios que afecten el escritorio, incluye
una comprobación en Windows.

## Integración continua

`.github/workflows/ci.yml` ejecuta esas mismas verificaciones en cada pull request
hacia `develop` o `main`, y en cada push a `develop`. Incluye suite en
Ubuntu y Windows, build del instalador y smoke real de instalación/desinstalación.
Las versiones se preparan antes de promover `develop → main` mediante PR.
El merge a `main` autoriza la publicación: Release reutiliza CI y, si todo pasa,
crea automáticamente el tag y la release. Consulta [Releases](docs/releases.md)
para la política de versiones y reintentos.

**Un PR no se fusiona si el CI está en rojo.** Si un check falla, corrígelo en la
misma rama `feature/*` y espera una ejecución verde. No desactives un check para
poder mergear.

## Cálculo e interfaz

El backend calcula e interpreta los resultados matemáticos. El servidor valida
la entrada y los servicios de cada interfaz adaptan el resultado para mostrarlo.
Redondea solo para presentar y distingue el cambio entre iteraciones del
residuo y de la tolerancia que se usa en el criterio de parada.

Antes de crear un componente, revisa las [pautas para añadir una herramienta](docs/desarrollo.md#añadir-una-herramienta)
y los [componentes de interfaz](docs/interfaz.md). Reutiliza el catálogo, los
layouts, el teclado, los editores, el menú de edición y el formato numérico que
corresponda. Conserva el formulario y la lectura básica del resultado sin
JavaScript y aplica el presupuesto del proyecto a las operaciones costosas.

## Bibliotecas matemáticas y algoritmos educativos

La antigua prohibición de NumPy, SciPy y SymPy ya no aplica. Pueden utilizarse
bibliotecas matemáticas cuando ayuden a la tarea; declara sus dependencias con uv.
La bisección sí se implementa manualmente: ninguna biblioteca sustituye su ciclo
de punto medio, evaluación y selección del subintervalo. Los algoritmos existentes
conservan sus implementaciones y sus verificaciones matemáticas.

`fractions.Fraction` representa racionales exactos. Los métodos numéricos trabajan
con aproximaciones de máquina y deben distinguir tolerancia, error y residuo.
La interpretación de entradas no debe ejecutar código arbitrario (`eval`/`exec`).
`tests/test_restricciones_proyecto.py` conserva comprobaciones de seguridad y
separación entre backend y presentación, sin prohibir paquetes por su nombre.

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
- la interpretación mantiene su parser seguro, sin `eval` ni `exec`;
- el parser solo lee la sintaxis de cada lado del `=`; agrupar términos y pasar
  la igualdad a la forma estándar lo hacen `expresion_desde_terminos` y
  `normalizar_igualdad` de `backend/expresiones.py`, que otro parser de
  ecuaciones lineales puede reutilizar tal cual.

La conversión de texto a número está centralizada en `convertir_a_numero`. Si hace
falta leer un número en otro sitio, reutilízala en vez de escribir otro parser.

El parser devuelve solo la matriz aumentada, sin metadata sobre su origen: el
backend matemático no debe saber si el sistema se escribió como texto o se ingresó
coeficiente por coeficiente.

## Calidad del código

Estas convenciones buscan que un estudiante pueda seguir el cálculo en el código
y que un cambio no altere lo que la persona usuaria ve. Ante la duda, elige la
versión más simple que cumpla las pruebas.

**Funciones con una responsabilidad clara.** Si para describir una función hace
falta decir «y además», probablemente son dos. `ExpresionMatricialForm.clean`
muestra de arriba abajo sus fases (campos, operandos, acciones de edición y
cálculo) y delega cada una en un método con nombre propio. No partas una función
solo por su longitud: el bucle de un método numérico puede ser largo y seguir
expresando una sola idea, en el mismo orden en que se explica en clase.

**Nombres descriptivos y fieles a la notación.** Usa nombres de dominio en
español. Conserva `A`, `b`, `x`, `i`, `j` o `k` cuando una fórmula cercana fija
qué representan o qué indexan. Si una variable cambia de papel, nómbrala por ese
papel: en Secante, `anterior` y `actual` son los dos puntos que definen la
próxima recta. No renombres funciones públicas, campos de formulario, claves de
resultados ni rutas sin un motivo funcional: la consola, las plantillas, las
pruebas y los enlaces guardados dependen de ellos.

**Comentarios breves sobre lo que el código no dice.** Una línea junto a una
fórmula, a una condición de parada, al significado de una variable o a una
decisión que no se deduce del código. No repitas lo que ya dice la llamada:

```python
# Recorre cada fila
for fila in matriz:
```

Un comentario útil explica una decisión matemática:

```python
# El estado es la pareja ordenada (xₙ₋₁, xₙ): una abscisa que reaparece con otra compañera
# define otra recta y puede dar un punto nuevo. Solo una pareja repetida cierra un ciclo.
```

**Docstrings en los contratos públicos.** Una función que usan otras capas
indica qué entrada admite, qué tipo de número usa (`Fraction` exacto o
aproximación de máquina), cuándo se detiene, qué devuelve al fallar y qué
excepciones lanza. Si la tabla completa de estados o claves ya está en `docs/`,
enlázala en lugar de copiarla. Un ayudante privado cuyo nombre basta no necesita
docstring, y ninguno debe ser largo solo por decorar.

**Cálculo, validación y presentación separados.** `backend/` calcula e
interpreta; los formularios validan y normalizan la entrada; los servicios,
plantillas y JS presentan. Redondea solo para mostrar y no decidas una
clasificación en la plantilla. Consulta [Cálculo e interfaz](#cálculo-e-interfaz).

**Reutiliza cuando la responsabilidad es la misma.** Comparte código si dos
usos representan la misma decisión: `aplicar_gauss_jordan` parte de
`aplicar_gauss`, y Newton y Secante comparten `impedimento_paso_abierto`. Si
solo se parecen, mantenlos separados: Bisección y Regla falsa comparten la
preparación del intervalo, pero no el bucle, porque cortan, miden el error y
confirman la cercanía de forma distinta.

**Pruebas que protegen lo observable.** Comprueba lo que ve quien usa o consume
la herramienta: valores, orden de los pasos, clasificación, el campo y el texto
de un error, y en el navegador, foco, cursor y selección. Evita aserciones sobre
nombres privados o sobre el espaciado del HTML; usa el DOM o los datos
decodificados. Antes de reestructurar, escribe una prueba de caracterización
que pase con el código actual y consérvala en el PR.

**Sin sobreingeniería.** No añadas capas, clases base, configuraciones ni
parámetros para casos que todavía no existen. Una herramienta nueva reutiliza el
catálogo, los layouts y los componentes actuales; no necesita un sistema de
plugins ni un motor matemático universal. Una optimización necesita una medición
que muestre dónde está el costo antes de cambiar el diseño.

## Configuración local

Las configuraciones de editores (`.idea/`) y de asistentes de IA (`CLAUDE.md`,
`.claude/`, `AGENTS.md`, `.cursor/`, entre otros) están en `.gitignore` y no se
versionan. La documentación compartida vive en `README.md`, este archivo y
[docs/](docs/README.md).

## Herramientas que podríamos añadir más adelante

El proyecto todavía no usa linters ni formateadores, a propósito: por ahora las
verificaciones son pruebas y compilación. Si en algún momento hace falta, serían
candidatos razonables, en este orden:

- un formateador y linter (por ejemplo Ruff) para unificar estilo;
- cobertura de pruebas en el CI;
- `pre-commit` para correr las verificaciones antes de cada commit.

Ninguno es un requisito actual. Si se añade alguno, debe entrar como cambio propio
y no colado dentro de otra tarea.
