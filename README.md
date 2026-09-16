# Álgebra Lineal

Proyecto educativo en Python para implementar manualmente algoritmos de matrices
y álgebra lineal. El objetivo no es resolver operaciones rápido, sino escribir el
algoritmo paso a paso y entender cómo funciona por dentro.

La aplicación se puede usar desde la terminal, mediante un menú interactivo, o
desde una interfaz desktop local. Django sigue siendo la capa de presentación;
la ventana nativa solo muestra esa interfaz, con identidad visual propia, tema
claro/oscuro y funcionamiento completo sin Internet. La estructura de la
interfaz está pensada para ir añadiendo más temas del curso como módulos, sin
rediseñar la aplicación cada vez.

## Funcionalidades actuales

- Generar una matriz con valores aleatorios a partir de sus dimensiones.
- Crear una matriz ingresando cada elemento manualmente.
- Crear un sistema de ecuaciones, escribiéndolo directamente como texto o
  ingresando sus coeficientes uno por uno.
- Modificar un elemento en una posición dada.
- Consultar un elemento en una posición dada.
- Mostrar la matriz completa con las columnas alineadas.
- Resolver el sistema por **Gauss**, mostrando la eliminación hacia abajo, la
  matriz escalonada y la sustitución regresiva.
- Resolver el sistema por **Gauss-Jordan**, mostrando la reducción completa y la
  matriz reducida.
- Mostrar las columnas pivote en web, escritorio y terminal, numeradas desde 1,
  sin incluir la columna de términos independientes.
- Traducir la matriz resultante de vuelta a su sistema de ecuaciones, clasificarlo
  y mostrar el conjunto solución completo: valores exactos cuando la solución es
  única, variables libres identificadas y variables pivote despejadas en función
  de ellas cuando hay infinitas, y la contradicción a la vista cuando no hay
  solución.
- Resolver sistemas desde la interfaz desktop o Django mediante texto o una
  matriz aumentada editable, sin reemplazar la interfaz de terminal.
- Usar una interfaz visual propia, con tema claro u oscuro, matrices con
  notación de corchetes y el procedimiento paso a paso como pieza central.
- Sumar, restar, multiplicar por un escalar y trasponer matrices rectangulares
  con fracciones exactas y desarrollo de cada entrada desde web y escritorio.
- Multiplicar matrices (`AB`) y una matriz por un vector (`Ax`), con la
  compatibilidad de dimensiones a la vista y el procedimiento explicado de dos
  maneras equivalentes: fila por columna (regla fila-vector) o por columnas
  (combinación lineal de las columnas de A), o ambas para compararlas.
- Resolver la ecuación matricial `Ax = b` con A y b conocidos y x desconocido,
  incluso con A rectangular: se escribe como ecuación vectorial, sistema
  equivalente y matriz aumentada `[A | b]`, se resuelve con Gauss, Gauss-Jordan
  o ambos, y se interpreta si b es combinación lineal de las columnas de A.
- Convertir números enteros entre decimal y binario, octal o hexadecimal desde
  la interfaz web y desktop, mostrando las divisiones sucesivas o la expansión
  posicional (combinación lineal) que justifica el resultado.
- Sumar y restar vectores, multiplicarlos por un escalar y comprobar si un
  vector es combinación lineal de otros, en cualquier dimensión `n`, con
  aritmética exacta y el procedimiento a la vista.

El menú de la terminal es este:

```text
1. Generar matriz
2. Crear matriz
3. Crear sistema de ecuaciones
4. Modificar elemento
5. Consultar elemento
6. Ver matriz
7. Resolver por Gauss
8. Resolver por Gauss-Jordan
9. Salir
```

Los cálculos usan `fractions.Fraction`, así que los resultados son exactos y se
muestran como fracciones cuando no son enteros.

La interfaz de terminal usa colores, limpia la pantalla entre secciones y espera
una confirmación antes de volver al menú, para que los resultados se puedan leer
con calma.

## Sistemas de ecuaciones

La opción `Crear sistema de ecuaciones` abre un submenú:

```text
1. Ingresar sistema directamente
2. Ingresar coeficientes manualmente
3. Volver
```

En el ingreso directo se escribe el sistema completo, separando las ecuaciones
con `;`:

```text
x1 - 3x2 - 5x3 = 0; x2 + x3 = 3
```

que produce esta matriz aumentada:

```text
[  1  -3  -5   0 ]
[  0   1   1   3 ]
```

Las variables son `x1`, `x2`, `x3`, … con índice desde 1. Se admiten espacios
libres, coeficientes implícitos (`x1` vale `1x1` y `-x2` vale `-1x2`), variables
ausentes (valen cero), enteros, fracciones (`1/2x1`) y decimales (`0.5x1`). El
lado derecho del `=` debe ser un número.

El ingreso manual pide la cantidad de variables y de ecuaciones, y luego cada
coeficiente y cada término independiente. Ambas formas producen exactamente la
misma matriz aumentada, así que son intercambiables.

Volver al menú, o escribir un sistema con un formato inválido, deja intacta la
matriz activa: solo un sistema creado correctamente la reemplaza.

## Resolver un sistema

Una matriz solo se interpreta como sistema de ecuaciones cuando se elige uno de
los dos métodos de resolución. En ese caso la **última columna** se toma
explícitamente como los términos independientes; el significado nunca se deduce
de las dimensiones. Por eso una matriz `3 x 3` puede ser una matriz cualquiera o
el sistema de 3 ecuaciones y 2 variables, según la opción que se use. Da igual si
la matriz se creó con `Crear matriz` o con `Crear sistema de ecuaciones`.

La diferencia entre los dos métodos está en el procedimiento:

- **Gauss** solo elimina hacia abajo y deja la matriz escalonada. Cuando la
  solución es única muestra además la sustitución regresiva paso a paso.
- **Gauss-Jordan** continúa eliminando hacia arriba hasta la forma reducida.

Para el mismo sistema los dos llegan siempre a la misma clasificación y a la
misma solución final.

La clasificación del sistema es una de estas tres:

```text
Consistente de solución única
Consistente de soluciones infinitas
Inconsistente
```

## Interpretación del resultado

La salida se adapta a la clasificación obtenida. La matriz, la clasificación y
la solución siempre se muestran; el **sistema resultante** se conserva cuando
ayuda a interpretar una forma escalonada, una variable libre o una
contradicción. Si la matriz ya permite leer directamente `x1 = C1`, `x2 = C2`,
etc., no se repiten esas mismas ecuaciones antes de la solución.

Por ejemplo, una solución única leída directamente se presenta de forma breve:

```text
Consistente de solución única

x1 = 3
x2 = 2/3
```

En Gauss, el sistema resultante sí se mantiene cuando permite seguir la
sustitución regresiva. Las filas nulas (`0 = 0`) no cambian por sí solas la
clasificación: si todas las variables tienen pivote, la solución sigue siendo
única.

La **solución** es la interpretación final del conjunto solución. Si falta algún
pivote, las variables de esas columnas quedan libres y las demás se despejan en
función de ellas:

```text
Sistema resultante

x1 - 5x3 = 1
x2 + x3 = 4

Clasificación

Consistente de soluciones infinitas

Solución

La variable x3 no tiene pivote, por lo que es libre.

x1 = 1 + 5x3
x2 = 4 - x3
x3 es libre
```

El despeje es simbólico y sigue hasta que ninguna variable pivote dependa de otra
variable pivote. Para `x1 + x2 + x3 = 5` junto a `x2 + x3 = 2`, la solución es
`x1 = 3`, no `x1 = 5 - x2 - x3`. Todo se calcula con fracciones exactas, y las
variables se listan de `x1` a `xn` aunque algunas sean libres.

Cuando existe una fila contradictoria, se muestra su posición y su contenido
exacto. Por ejemplo:

```text
0 = 5

En la fila 3 se obtiene [0 0 0 | 5], que equivale a 0 = 5.

Como esta igualdad es imposible, el sistema es inconsistente y no tiene solución.
```

La evidencia estructurada —fila contradictoria, filas redundantes, columnas sin
pivote y valores como `Fraction`— se calcula en `backend/`. La terminal solo la
presenta, de modo que cualquier otra interfaz puede reutilizar la misma
interpretación sin reconstruir conclusiones matemáticas.

Gauss-Jordan sigue sirviendo para reducir **cualquier matriz rectangular**
(`2 x 3`, `3 x 2`, `4 x 3`, etc.), sin exigir matrices cuadradas ni de la forma
`n x (n+1)`, y sin suponer que toda fila o toda columna acabe con pivote. Esa
capacidad vive en `backend/gauss_jordan.py` y se puede reutilizar, aunque el menú
esté orientado a resolver sistemas.

## Vectores

La herramienta **Operaciones con vectores** (`/vectores/operaciones/`) es la
única de la categoría Vectores: la operación se elige dentro, igual que el
método en Resolver un sistema. La dimensión `n` no está fijada —el profesor
no la conoce de antemano—, así que cada vector se escribe como una fila de
celdas, `u = ( [ ] [ ] [ ] )`, y los botones **+/−** agregan o quitan
componentes (de 1 a 10). No hay campos `x`, `y`, `z` ni sintaxis de listas.

- **Suma** y **resta** operan componente a componente y exigen la misma
  dimensión: `(1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)`.
- **Multiplicación por escalar** multiplica cada componente por `k`:
  `3(1, -2, 4) = (3·1, 3·(-2), 3·4) = (3, -6, 12)`.
- **Combinación lineal** pregunta si `b` es combinación lineal de `v1 … vk`
  (de 1 a 6 vectores, con **+/− vector**). No hay un segundo algoritmo de
  eliminación: `c1·v1 + … + ck·vk = b` se escribe como la matriz aumentada
  `[v1 v2 … vk | b]` —cada generador es una columna y `b` la columna
  aumentada— y se resuelve con el Gauss-Jordan de `backend/sistemas.py`. La
  clasificación del sistema decide la respuesta:
  - solución única: **sí**, y se muestran `c1, c2, …` y la igualdad
    `(3, 4) = 3(1, 0) + 4(0, 1)`;
  - soluciones infinitas: **sí**, con la solución general en función de los
    coeficientes libres y una combinación concreta (libres en cero);
  - inconsistente: **no**, porque el sistema asociado no tiene solución.

El procedimiento habla el lenguaje del ejercicio —coeficientes `c1, c2, …`,
no variables `x1, x2, …`—: planteamiento, sistema equivalente, matriz
aumentada, operaciones por filas, matriz reducida y lectura del resultado.
Todo se calcula con `fractions.Fraction`: `(1/2, 2/3) + (1/2, 1/3) = (1, 1)`.

El núcleo vive en `backend/vectores.py` (listas, ciclos y `Fraction`, sin
librerías externas). El formulario reconstruye la estructura esperada
(dimensión y cantidad de vectores) y la compara con lo recibido, así que un
POST con celdas de más, de menos o con otros nombres se rechaza; las
dimensiones incompatibles se detectan antes de intentar resolver.

## Sistemas numéricos

La herramienta **Conversión de bases** (`/bases/conversion/`) convierte enteros
no negativos entre binario, octal, decimal y hexadecimal: se escribe el número y
se eligen la base de origen y la de destino (distintas; un botón las
intercambia). Solo hay dos algoritmos, y cualquier par de bases se resuelve con
ellos:

- **Decimal → binario, octal o hexadecimal**, por divisiones sucesivas: se
  divide el número entre la base, se guarda el residuo y se repite con el
  cociente hasta llegar a cero; el resultado se lee tomando los residuos del
  último al primero. `13₁₀ → 1101₂`.
- **Binario, octal o hexadecimal → decimal**, por expansión posicional: cada
  dígito se multiplica por la potencia de la base que corresponde a su posición
  y se suman los aportes. `1011₂ = 1·2³ + 0·2² + 1·2¹ + 1·2⁰ = 8 + 0 + 2 + 1 =
  11₁₀`.
- **Entre dos bases no decimales**, encadenando los dos: primero la expansión
  hacia decimal y después las divisiones hacia la base destino, con el valor
  intermedio a la vista. `1010₂ = 10₁₀ = A₁₆`.

En hexadecimal los residuos y dígitos `10`–`15` se escriben `A`–`F`; la entrada
acepta minúsculas y el resultado se normaliza a mayúsculas. El procedimiento
muestra esa sustitución (`10 → A`, `A = 10`) y siempre queda visible junto al
resultado. Los dígitos inválidos para la base elegida, la entrada vacía y los
números negativos se rechazan con un mensaje claro; no se admiten fracciones ni
otras bases.

El núcleo vive en `backend/sistemas_numericos/` y devuelve los pasos como datos
(dividendo, cociente, residuo y símbolo; o dígito, valor, posición, potencia y
aporte), sin HTML. No usa `bin`, `oct`, `hex` ni `int(texto, base)`: la
conversión se construye a mano, y `tests/test_sistemas_numericos.py` lo
comprueba con `ast`. El teclado en pantalla solo ofrece los dígitos válidos para
la base de origen (`0 1`, `0`–`7`, `0`–`9` o `0`–`F`) y, al cambiarla, la
entrada se revisa al instante; el servidor vuelve a validar al convertir.

## Para usuarios finales: instalar en Windows

1. Descarga `AlgebraLineal-Setup-x.y.z.exe` de la distribución del proyecto.
2. Ejecuta el instalador: decide si quieres un acceso directo en el escritorio y
   pulsa **Instalar**.
3. Abre **Álgebra Lineal** desde el menú Inicio o el acceso directo opcional del escritorio.

No necesitas Git, Python, uv, PyInstaller, terminal ni acceso al repositorio.
El instalador no pide elegir una carpeta: la aplicación se instala para tu usuario
en `%LOCALAPPDATA%\Programs\AlgebraLineal`, sin solicitar privilegios de
administrador, y la pantalla **Listo para Instalar** muestra esa ubicación antes
de continuar. El asistente sigue el tema claro u oscuro de Windows y la aplicación
funciona sin una consola detrás.
Para quitarla, usa **Configuración → Aplicaciones → Álgebra Lineal → Desinstalar**.

Requiere Windows 10 1809 o posterior / Windows 11, compatible con aplicaciones x64.
Si falta **Microsoft Edge WebView2 Runtime**, el instalador te avisa y ejecuta el
bootstrapper oficial de Microsoft incluido en el paquete. Solo en ese caso
necesitas Internet durante la instalación. Una vez instalado, la calculadora
funciona sin Internet. En un equipo sin conexión, instala previamente WebView2
con el instalador **Evergreen Standalone** de
[Microsoft](https://developer.microsoft.com/microsoft-edge/webview2/).

Si Microsoft no puede instalar el runtime, la instalación muestra instrucciones
para corregirlo y volver a intentarlo. El ejecutable también comprueba el runtime
antes de iniciar y muestra un mensaje legible si falta. La desinstalación elimina
los archivos y accesos directos de Álgebra Lineal; conserva WebView2, que puede ser
utilizado por otras aplicaciones.

Los instaladores se distribuyen manualmente por los mantenedores; CI no publica
Releases. El paquete actual no está firmado digitalmente: Windows puede mostrar
el editor como desconocido.

## Para desarrolladores

### Requisitos

- [uv](https://docs.astral.sh/uv/) instalado. Consulta su documentación oficial
  para instalarlo en tu sistema.
- Python 3.13. La versión está fijada en `.python-version`, y `uv` la descarga por
  ti si todavía no la tienes.
- `colorama`, usada solo para dar color a la terminal.
- `Django`, usado únicamente como capa de presentación web.
- `waitress`, usado como servidor WSGI local de la aplicación desktop.
- `pywebview`, usado para mostrar Django en una ventana nativa.
- `PyInstaller`, disponible como dependencia de desarrollo para generar Windows.

Los cálculos y la interpretación de los sistemas siguen apoyándose en nuestra
implementación del backend y en la biblioteca estándar (`random`, `fractions` y
`re`).

### Preparar el entorno

Desde la raíz del repositorio:

```bash
uv sync --locked
```

`pyproject.toml` declara qué necesita el proyecto y `uv.lock` fija las versiones
exactas que se resolvieron a partir de esa declaración. `uv sync` construye el
entorno en `.venv/` usando ambos archivos, así que todos los colaboradores
trabajan con las mismas versiones.

### Ejecutar desde el código fuente

Desde la raíz del repositorio:

#### Terminal

```bash
uv run python main.py
```

Para salir, elige la opción `9` del menú.

#### Django en desarrollo

Desde la raíz del repositorio, inicia el servidor de desarrollo:

```bash
uv run python manage.py runserver
```

Abre <http://127.0.0.1:8000/> en el navegador. Inicio permite buscar una
herramienta o explorar el catálogo por área y categoría; la barra lateral
repite ese árbol en todas las páginas. Dentro de **Álgebra Lineal → Sistemas de
ecuaciones** hay una sola herramienta, **Resolver un sistema** (`/sistemas/`),
que se configura en el propio formulario:

| Opción | Valores | Predeterminado |
| --- | --- | --- |
| Método | Gauss, Gauss-Jordan o Comparar ambos | Gauss-Jordan |
| Mostrar | Procedimiento, Clasificación, Columnas pivote, Sistema resultante | Todos activos |

La matriz final y la solución se muestran siempre. **Comparar ambos** resuelve
la misma entrada con los dos métodos y presenta un procedimiento por método;
como la clasificación y la solución coinciden, aparecen una sola vez al final.
Las rutas de la versión anterior (`/sistemas/gauss/`, `/sistemas/gauss-jordan/`,
`/sistemas/clasificacion/` y `/sistemas/columnas-pivote/`) redirigen a
`/sistemas/`, las dos primeras con el método ya seleccionado.

Se puede elegir el tipo de entrada —sistema de ecuaciones o matriz aumentada— y
ambos validan igual. El selector de tema recuerda la preferencia en el
navegador; si no hay una elección previa, respeta el modo claro u oscuro del
sistema. En el modo matricial indica las dimensiones (o usa los botones
**+/−** de ecuaciones y variables) y completa una cuadrícula con la última
columna reservada para los términos independientes:

```text
       x1   x2   b
F1    [ 1 ] [ 2 ] | [ 4 ]
F2    [ 2 ] [-1 ] | [ 7 ]
```

Ambas entradas producen el mismo resultado. Django solo coordina la entrada y
la presentación: la capa de integración converge en una matriz aumentada y
delega los cálculos a `backend/`.

El **teclado matemático** que acompaña a cada campo muestra notación
matemática (`x₁`, `−`, `a⁄b`) e inserta la sintaxis que entiende el parser
(`x1`, `-`, `/`), de modo que nadie necesita conocer esa sintaxis para escribir
un sistema. Solo aparece con JavaScript y solo contiene teclas con una
inserción real.

Después de resolver, **Continúa con este mismo sistema** envía la entrada
actual a otra herramienta de la categoría (ver el procedimiento con
Gauss-Jordan, identificar las columnas pivote, analizar el tipo de solución):
el texto permanece visible y la matriz conserva sus dimensiones, valores y
fracciones; Gauss y Gauss-Jordan imponen su método aunque llegue otro.

La barra lateral agrupa las herramientas por área y categoría con secciones
expandibles; la categoría activa llega abierta y las que el usuario abre se
recuerdan. El botón **Menú** la oculta en escritorio para ganar espacio y, hasta
880 px, la abre como un cajón sobre el contenido; Escape o el fondo lo cierran
y devuelven el foco al botón. El buscador filtra las herramientas al instante y,
sin JavaScript, envía la consulta a Inicio (`/?q=gauss`), que responde con los
mismos resultados. Sin JavaScript la navegación permanece visible y se puede
resolver y compartir la entrada desde texto; la cuadrícula editable, el
teclado y los botones de estructura requieren JavaScript.

### Organización modular y nuevas herramientas

El recorrido web y desktop es **Inicio → área → categoría → herramienta →
resultado**, y el breadcrumb lo reproduce con enlaces reales (las áreas y
categorías llevan a su sección del Inicio). Matrices ofrece **Operaciones con
matrices** y **Resolver Ax = b**, vectores ofrece Operaciones con vectores y
sistemas numéricos, la conversión de bases. Límites continúa como
**Próximamente**.

`frontend/web/calculadora/catalogo.py` es el registro central: las estructuras
inmutables `Area`, `Categoria` y `Herramienta` definen identidad, descripción,
estado, nombre de ruta Django, palabras clave, relaciones por ID y la frase
con la que se sugiere una herramienta desde otra. No usan base de datos. La
barra lateral, el buscador (`buscar_herramientas`, sin acentos ni mayúsculas),
el Inicio, los breadcrumbs y las herramientas relacionadas derivan de ahí:
`context_processors.navegacion` identifica la herramienta activa a partir de la
ruta resuelta, así que las vistas no arman la navegación a mano.

Para agregar una herramienta:

1. Crea su vista y ruta con nombre en `calculadora/urls.py`, y su template en
   `templates/calculadora/modules/<modulo>/`, extendiendo
   `calculadora/layouts/herramienta.html` y rellenando solo los bloques que
   necesite: `tool_context`, `tool_input`, `tool_result`, `tool_explanation` y
   `tool_related`.
2. Regístrala una sola vez en `HERRAMIENTAS`, con ID único y una categoría de
   `CATEGORIAS`. Usa `disponible` y una ruta resoluble cuando funcione;
   `proximamente` no genera enlaces. Una ruta no registrada responde 404.
3. Declara `palabras_clave` con sinónimos que un estudiante escribiría; el
   nombre, la categoría y el área ya forman parte del índice de búsqueda.
4. Define relaciones con IDs existentes en `relacionadas` y una `invitacion`
   breve; `relacionadas_disponibles` excluye destinos aún no disponibles. Las
   relaciones se reservan para módulos realmente distintos: las variantes de
   una misma herramienta (método, bloques del resultado) son opciones de su
   formulario, no herramientas aparte.
5. Si la herramienta necesita símbolos, declara un `TecladoContextual` en
   `teclados.py` con solo las teclas que usa e inclúyelo con
   `components/math_keyboard.html` dentro del contenedor de sus campos. Los
   controles que cambian la estructura (más filas, menos columnas) van aparte,
   nunca dentro del teclado.
6. Añade pruebas de rutas, navegación, búsqueda y comportamiento. Mantén la
   matemática en `backend/` y la presentación en los templates del módulo.

Resolver un sistema sigue ese patrón con una sola vista: `opciones_sistemas.py`
declara los métodos, los bloques del resultado, sus valores predeterminados y
las rutas antiguas que redirigen a la herramienta. Operaciones con vectores
hace lo mismo con `opciones_vectores.py` (operaciones, límites de dimensión y
de vectores, nombres de los vectores por operación) y `servicios_vectores.py`
(presentación: vectores como `(1, 2, 3)`, desarrollo componente a componente,
planteamiento y conclusión de la combinación lineal).

**Operaciones con matrices** (`/matrices/operaciones/`) reúne suma, resta,
producto por escalar, traspuesta, multiplicación de matrices (`AB`) y matriz
por vector (`Ax`) en un solo formulario. Filas y columnas se eligen de 1 a 10
por legibilidad; el backend no impone ese límite ni exige matrices cuadradas.
Para suma/resta, A y B comparten dimensiones. En `AB` la interfaz pide tres
medidas —filas de A, columnas de A (= filas de B) y columnas de B— y muestra
`A: m×n · B: n×p → AB: m×p`, así que no se puede construir un producto
imposible; en `Ax` el vector columna x toma su dimensión de las columnas de A
(`A (m×n) · x (n) → Ax (m)`). Con JavaScript los controles +/− regeneran las
celdas y conservan los valores; sin JavaScript, **Aplicar** prepara la
estructura antes de calcular. El teclado contextual existente permite
negativos y fracciones.

Para `AB` y `Ax` se elige cómo ver el procedimiento, igual que el método en
Resolver un sistema: **Fila por columna** (`cᵢⱼ = filaᵢ(A) · columnaⱼ(B)`,
que en `Ax` se llama **Regla fila-vector**), **Por columnas**
(`AB = [Ab₁ Ab₂ … Abₚ]`, con cada `Abⱼ` como combinación lineal de las
columnas de A; en `Ax`, **Combinación lineal de columnas**:
`Ax = x₁a₁ + … + xₙaₙ`) o **Comparar ambos**. Son dos lecturas del mismo
producto, no dos operaciones: el resultado se calcula una sola vez y se muestra
una sola vez; cada método muestra su procedimiento con la igualdad completa de
cada entrada (`c₂₃ = fila₂(A) · columna₃(B) = a₂₁b₁₃ + … = 3·2 + (-1)·4 +
5·(1/2) = 9/2`) o de cada columna (`Ab₁ = 2a₁ − a₂ + 3a₃`, los vectores
escalados y la columna obtenida). Los grupos por fila o por columna se
despliegan con `details` y nacen abiertos cuando el resultado tiene pocas
entradas.

`backend/matrices.py` contiene las seis operaciones y los pasos estructurados
con `Fraction`: `producto_punto` es la primitiva, `multiplicar_matrices`
calcula `cᵢⱼ` como producto punto de fila por columna y
`multiplicar_matriz_vector` reutiliza ese mismo producto con x escrito como
columna, cambiando solo la validación y la explicación. Los productos
`aᵢₖbₖⱼ` se calculan una vez y se entregan agrupados por entrada y por
columna. `forms_matrices.py` valida dimensiones, método, campos y números con
el parser común; `opciones_matrices.py` centraliza la configuración y
`servicios_matrices.py` adapta los datos a presentación. El resultado aparece
antes del procedimiento: expresión matricial, regla por entrada y desarrollo;
la traspuesta explica el intercambio de filas/columnas y de dimensiones.
Los componentes de entrada y `components/matriz.html` se pueden reutilizar (x
se captura y se muestra como matriz `n×1`); `matrix.html` mantiene la
representación aumentada de sistemas. Las igualdades y matrices anchas se
desplazan dentro de sus contenedores.

En `Ax` el vector x es conocido y solo se calcula el producto. Buscar x es
otra herramienta: **Resolver Ax = b** (`/matrices/ecuaciones/`), la segunda
de la categoría Matrices. Allí A (m×n) y b son conocidos, x es la incógnita y
la interfaz muestra `A (m×n) · x (n) = b (m)`: se eligen solo las dimensiones
de A, b toma m componentes, x se dibuja como vector de incógnitas `x₁ … xₙ` sin
celdas editables y A no necesita ser cuadrada (`2×3`, `3×2`, …). La
herramienta enseña que estas formas son la misma ecuación:

```text
Ax = b  ↔  x₁a₁ + x₂a₂ + … + xₙaₙ = b  ↔  sistema lineal  ↔  [A | b]
```

No hay un segundo solucionador: `backend/ecuaciones_matriciales.py` valida la
ecuación, construye `[A | b]` con listas y `Fraction` y la entrega a
`resolver_sistema_gauss` o `resolver_sistema_gauss_jordan` de
`backend/sistemas.py`, cuyo resultado se amplía con la lectura de `Ax = b`.
Vive en una capa aparte porque `sistemas.py` ya depende de utilidades de
`matrices.py`. El método se elige como en Resolver un sistema (Gauss,
Gauss-Jordan, predeterminado, o Comparar ambos, que muestra el resultado una
sola vez y los dos procedimientos). El resultado va antes del procedimiento:

- solución única: `Ax = b tiene solución única.`, las líneas `x1 = 3`,
  `x2 = 2`, el vector columna x y la comprobación `A · x = b` calculada con
  `multiplicar_matriz_vector`; b es combinación lineal de las columnas de A de
  una única manera (`b = 3a₁ + 2a₂`);
- soluciones infinitas: la solución general de sistemas (`x1 = 2 - x3`,
  `x3 es libre`); b es combinación lineal de las columnas de A de infinitas
  maneras;
- inconsistente: la contradicción que ya detecta sistemas (`[0 0 | 1]`, es
  decir, `0 = 1`); b no pertenece al conjunto generado por las columnas de A.

La interpretación como combinación lineal se deriva solo de la clasificación
del sistema. El procedimiento muestra la cadena de equivalencias —ecuación
matricial, ecuación vectorial con las columnas de A, sistema equivalente
(`ecuaciones_de_matriz`, con `n` incógnitas) y matriz aumentada— y después la
eliminación con los mismos bloques de Resolver un sistema: operaciones por
filas, matriz escalonada o reducida con sus pivotes, columnas pivote, sistema
resultante y sustitución regresiva. `EcuacionMatricialForm`
(`forms_ecuaciones.py`) comparte con `MatricesForm` la base `FormularioCeldas`
—celdas, parser y comprobaciones del POST— y exige que b tenga exactamente
una componente por fila de A; x nunca viaja en el POST. Con JavaScript los
controles +/− regeneran A, x y b; sin JavaScript, **Aplicar** redibuja la
misma estructura.

```text
templates/calculadora/
├── base.html                 # header, sidebar, breadcrumbs y contenido
├── layouts/herramienta.html  # estructura común de una herramienta
├── components/               # sidebar, buscador, breadcrumbs, relacionadas, teclado, matrices, vectores, guías
├── pages/inicio.html
├── modules/sistemas/         # index.html y parciales del procedimiento y el resultado
├── modules/vectores/         # index.html, fila de entrada, operación y combinación lineal
├── modules/matrices/         # entrada rectangular, resultado y procedimientos (P13A y P13B)
├── modules/ecuaciones/       # Ax = b: entrada A · x = b, equivalencias y eliminación reutilizada (P14)
└── modules/bases/            # index.html y procedimiento de la conversión
```

P10 renovó la identidad visual y P10.1 añadió la navegación escalable, el
registro central, el buscador, la estructura común de herramienta y el teclado
matemático contextual, conservando el comportamiento matemático. Los detalles
para desarrolladores están en [docs/interfaz.md](docs/interfaz.md).

#### Aplicación de escritorio durante desarrollo

Desde Windows, el launcher inicia Django con Waitress en un puerto efímero de
`127.0.0.1` y abre una ventana nativa con pywebview. No usa `runserver` ni abre
un navegador externo:

```bash
uv run python desktop.py
```

La readiness se comprueba con un `HTTP GET /` antes de crear la ventana. Al
cerrarla, el launcher llama a `server.close()` y espera el final del thread de
Waitress.

### Generar distribución de Windows

La cadena de distribución mantiene el launcher y su configuración `onedir` y
`windowed` en `AlgebraLineal.spec`:

```text
Código → PyInstaller → dist/AlgebraLineal/ → Inno Setup → instalador .exe
```

En una PC de desarrollo Windows con Python x64, instala **uv** e
[Inno Setup 6.3 o posterior](https://jrsoftware.org/isdl.php). Inno Setup convierte
la carpeta construida en un instalador con accesos directos y desinstalador.
CI utiliza Inno Setup 6.7.3. PowerShell 5.1 o posterior es suficiente.

Desde la raíz, un solo comando genera la distribución completa:

```powershell
.\scripts\build_windows.ps1
```

El script valida herramientas y Python x64, ejecuta `uv lock --check` y
`uv sync --locked --group dev`, limpia los artefactos de esa fase, construye el
`.spec`, verifica el ejecutable, prepara WebView2, compila Inno Setup y comprueba
el instalador. Cada comando conserva su salida y un fallo detiene el proceso.
La versión se lee de **`project.version` en `pyproject.toml`** y se pasa a Inno
Setup; no se mantiene otra copia manual. Se admiten versiones numéricas de tres
o cuatro componentes.

También puedes construir por fases:

```powershell
# Solo PyInstaller (no requiere Inno Setup):
.\scripts\build_windows.ps1 -Target App

# Solo instalador, usando el build ya existente:
.\scripts\build_windows.ps1 -Target Installer

# Si ISCC.exe está en una ubicación personalizada:
.\scripts\build_windows.ps1 -IsccPath 'C:\Herramientas\Inno Setup 6\ISCC.exe'
```

`-Target Installer` empaqueta la carpeta existente: si cambiaste el código,
ejecuta primero `-Target App` o usa el comando completo. El equivalente directo
para PyInstaller, después de sincronizar dependencias, sigue siendo:

```powershell
uv run --locked pyinstaller --noconfirm --clean AlgebraLineal.spec
```

La configuración del instalador vive en `installer/AlgebraLineal.iss`. El script
invoca `ISCC.exe` con `/DAppVersion` y `/DProjectRoot`; para evitar omisiones de
prerrequisitos se recomienda compilarla mediante `-Target Installer`.

El asistente usa `WizardStyle=modern dynamic windows11`, un estilo integrado en
Inno Setup que sigue el tema claro u oscuro de Windows sin archivos de estilo
externos. La página de carpeta está desactivada (`DisableDirPage=yes`): la
instalación por usuario va siempre a `%LOCALAPPDATA%\Programs\AlgebraLineal` y
la página **Listo para Instalar** muestra esa ubicación, los accesos directos y
el estado de WebView2 (`AlwaysShowDirOnReadyPage=yes` + `UpdateReadyMemo`). Al
instalar una versión sobre otra existente se reutiliza la carpeta y la entrada de
**Aplicaciones instaladas** de la instalación previa. Para instalaciones avanzadas
o automatizadas sigue funcionando el parámetro estándar de Inno Setup, con o sin
`/VERYSILENT`:

```powershell
.\dist\installer\AlgebraLineal-Setup-0.1.0.exe /DIR="C:\Otra\Ruta"
```

```text
dist/
├── AlgebraLineal/
│   ├── AlgebraLineal.exe
│   └── _internal/              # Python, dependencias, templates y recursos locales
└── installer/
    └── AlgebraLineal-Setup-0.1.0.exe
```

`build/` y `dist/` están ignorados por Git. El script descarga el bootstrapper
desde Microsoft, comprueba su firma Authenticode y lo reutiliza en
`build/prerequisites/`. Puedes borrar ese archivo para descargarlo de nuevo.
Al instalar, se ejecuta desde `{app}\prerequisites`, solo si falta WebView2; la
aplicación se ejecuta desde su carpeta instalada. La detección consulta las
claves oficiales `pv` de HKCU y HKLM (vista de 32 bits para la instalación por
equipo), exige un runtime compatible con pywebview y evita el fallback a MSHTML.
Consulta la [distribución de WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution).

El job de Windows de `.github/workflows/ci.yml` instala Inno Setup desde su
distribución oficial firmada, construye ambos artefactos y ejecuta las pruebas.
Conserva el instalador y el bootstrapper como artefactos de la ejecución durante
14 días para revisión. El job Linux conserva sus verificaciones. Ninguno crea
una Release.

### Comprobar la distribución real

En una cuenta Windows **sin una instalación previa de Álgebra Lineal**, ejecuta:

```powershell
.\scripts\test_windows_distribution.ps1 -InstallerPath .\dist\installer\AlgebraLineal-Setup-0.1.0.exe
```

La prueba instala en una carpeta nueva de `%LOCALAPPDATA%\Programs` fuera del
repositorio. Comprueba ambos accesos directos y que el ejecutable sea `windowed`,
abre desde Inicio, resuelve por Gauss y Gauss-Jordan, las cuatro operaciones
de P13A, los productos `AB` y `Ax` comparando métodos y la ecuación
`Ax = b` de P14 (solución fraccionaria comparando métodos y un caso
rectangular 3×2) a través del Django/Waitress empaquetado, solicita CSS/JS
(incluidos `matrices.js` y `ecuaciones.js`) e icono, cierra la ventana y
verifica que el proceso y el servidor terminan. Repite la apertura y luego desinstala comprobando que se
eliminaron archivos, registro y accesos directos. Si esta máquina ya tiene
Álgebra Lineal instalada, el script se detiene a propósito: necesita una
cuenta o entorno limpio para no modificar esa instalación.

Completa esa prueba con una revisión visual: instalar normalmente, abrir desde
el acceso directo, resolver un sistema, verificar **Columnas pivote: C1, C3**,
cambiar entre tema claro y oscuro, cerrar, reabrir y desinstalar. La prueba por
HTTP no sustituye la inspección visual de pywebview. Para probar ausencia real
de WebView2, utiliza una VM limpia; no desinstales el runtime compartido de tu PC.

## Pruebas

Desde la raíz del repositorio:

```bash
uv lock --check
uv sync --locked
uv run python -m unittest discover -v
uv run python manage.py check
```

Las de `tests/` cubren las reglas matemáticas del backend (validaciones, matrices
rectangulares, pivotes, escalonamiento, sustitución regresiva y clasificación de
sistemas), las expresiones lineales y su formato, la traducción de una matriz a
su sistema, el conjunto solución con variables libres, el parser de sistemas, la
equivalencia entre Gauss y Gauss-Jordan, el flujo de la terminal, la interfaz web
de Django —incluidas sus entradas textual y matricial—, la infraestructura
desktop, el registro de herramientas, la navegación, el buscador, los
breadcrumbs, el teclado matemático, las opciones de Resolver un sistema
—método, comparación, bloques del resultado y rutas antiguas—, la conversión de
bases —resultados, pasos del procedimiento, mensajes de error y su integración
web—, las operaciones con vectores —suma, resta, escalar, combinación lineal
con solución única, infinitas o inconsistente, dimensión arbitraria, fracciones
exactas, la reutilización del motor de sistemas, la estructura dinámica del
formulario y los POST manipulados—, las operaciones con matrices —suma, resta,
escalar y traspuesta en rectangulares, fracciones exactas, procedimiento por
entrada, catálogo, selector, estructura dinámica, errores asociados a celdas
y POST manipulados—, los productos `AB` y `Ax` —producto punto, dimensiones
compatibles e incompatibles, rectangulares, fracciones, equivalencia exacta
entre fila por columna y por columnas (también contra la combinación lineal de
`backend/vectores.py`), tercera dimensión, vector x, selector de método,
comparación con un solo resultado y POST manipulados—, la ecuación matricial
`Ax = b` —matriz aumentada `[A | b]`, casos cuadrados y rectangulares con
solución única, infinitas o inconsistente, fracciones, equivalencia exacta con
Resolver un sistema y entre Gauss y Gauss-Jordan, comprobación `A · x = b`,
interpretación como combinación lineal, b derivado de las filas y x de las
columnas, flujo Aplicar sin JavaScript y POST manipulados— y que la interfaz
no cargue fuentes ni scripts remotos.
Sirven para detectar regresiones cuando el proyecto crezca.

Para comprobar que todo el código compila:

```bash
uv run python -m compileall -q backend frontend tests main.py manage.py desktop.py
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

`colorama` también está permitido, pero únicamente para dar color a la terminal:
no participa en ningún cálculo ni sustituye ningún algoritmo.

`tests/test_restricciones_proyecto.py` comprueba esta regla de forma automática:
analiza los imports del código con `ast` y revisa las dependencias declaradas en
`pyproject.toml`, así que la prohibición ya no depende de una revisión manual.

## Estructura actual

El proyecto separa la lógica matemática de la interfaz:

```text
Algebra-Lineal/
├── main.py                     # punto de entrada de la aplicación
├── manage.py                   # punto de entrada de Django
├── desktop.py                  # launcher Waitress + pywebview
├── AlgebraLineal.spec          # configuración reproducible de PyInstaller
├── installer/                  # fuentes Inno Setup, sin binarios generados
├── scripts/                    # build completo y prueba real de distribución
├── pyproject.toml              # metadata y dependencias declaradas
├── uv.lock                     # versiones exactas resueltas por uv
├── .python-version             # versión de Python del proyecto
├── README.md
├── CONTRIBUTING.md
├── assets/                     # icono local de la aplicación
├── docs/
│   └── interfaz.md             # cómo reutilizar el sistema visual
├── .github/
│   └── workflows/
│       └── ci.yml              # integración continua
├── backend/
│   ├── matrices.py             # utilidades, validación, operaciones básicas y productos AB/Ax exactos
│   ├── operaciones_filas.py    # operaciones elementales y registro de pasos
│   ├── expresiones.py          # expresiones lineales exactas y su formato
│   ├── gauss.py                # escalonamiento hacia abajo
│   ├── gauss_jordan.py         # reducción completa y rango
│   ├── parser_sistemas.py      # texto de ecuaciones → matriz aumentada
│   ├── sistemas.py             # clasificación, sistema resultante y solución
│   ├── vectores.py             # suma, resta, escalar y combinación lineal sobre sistemas
│   ├── ecuaciones_matriciales.py # Ax = b como [A | b] sobre los motores de sistemas
│   └── sistemas_numericos/     # conversión de bases con pasos estructurados
│       ├── digitos.py          # equivalencia A–F y potencias enteras
│       ├── validacion.py       # bases y dígitos válidos, mensajes de error
│       └── conversion.py       # divisiones sucesivas y expansión posicional
├── frontend/
│   ├── terminal/               # interfaz de línea de comandos
│   │   ├── menu.py             # bucle del menú y navegación
│   │   ├── opciones.py         # qué hace cada opción del menú
│   │   ├── entradas.py         # lectura y validación de datos del usuario
│   │   ├── salida.py           # formateo e impresión de matrices y pasos
│   │   └── consola.py          # colores, limpieza de pantalla y pausas
│   └── web/
│       ├── algebra_web/        # configuración, rutas y entradas WSGI/ASGI
│       └── calculadora/        # registro de herramientas, vistas, teclados, templates y recursos
└── tests/
    ├── test_matrices.py
    ├── test_operaciones_matrices.py
    ├── test_matrices_web.py
    ├── test_multiplicacion_matrices.py
    ├── test_multiplicacion_matrices_web.py
    ├── test_ecuaciones_matriciales.py
    ├── test_ecuaciones_matriciales_web.py
    ├── test_operaciones_filas.py
    ├── test_expresiones.py
    ├── test_gauss.py
    ├── test_gauss_jordan.py
    ├── test_parser_sistemas.py
    ├── test_sistemas.py
    ├── test_entradas.py
    ├── test_opciones.py
    ├── test_menu.py
    ├── test_salida.py
    ├── test_consola.py
    ├── test_web.py
    ├── test_navegacion.py
    ├── test_teclado.py
    ├── test_resolver_sistema.py
    ├── test_sistemas_numericos.py
    ├── test_conversion_bases_web.py
    ├── test_vectores.py
    ├── test_vectores_web.py
    ├── test_identidad_visual.py
    ├── test_desktop.py
    ├── test_recursos_interfaz.py
    └── test_restricciones_proyecto.py

La guía breve de la interfaz —sistema visual, guía educativa, tokens y tema—
está en [docs/interfaz.md](docs/interfaz.md).
```

Dentro de `backend/` la dependencia también va en un solo sentido, donde `→`
significa «depende de»:

```text
vectores                →  sistemas
vectores                →  matrices
ecuaciones_matriciales  →  sistemas
ecuaciones_matriciales  →  matrices
sistemas  →  gauss_jordan  →  gauss  →  operaciones_filas  →  matrices
sistemas  →  expresiones   →  matrices
```

`vectores.py` no escalona nada por su cuenta: escribe la combinación lineal
como matriz aumentada y llama a `resolver_sistema_gauss_jordan`, pidiéndole
que nombre las incógnitas `c1, c2, …`. Gauss y Gauss-Jordan siguen escribiendo
`x1, x2, …` por defecto. La validación de un vector vive en `matrices.py`,
junto al producto punto, porque las filas y columnas de una matriz también son
vectores; `vectores.py` la importa de ahí. Los productos `AB` y `Ax` no
dependen de `vectores.py`: la explicación por columnas es la misma combinación
lineal, y las pruebas comprueban que coincide con `combinar` de ese módulo.
`ecuaciones_matriciales.py` tampoco escalona: escribe `Ax = b` como `[A | b]`
y llama al motor de sistemas elegido; al vivir por encima de `sistemas.py` y
de `matrices.py`, `matrices.py` no necesita importar `sistemas.py`.

Gauss-Jordan no repite el escalonamiento: llama a `aplicar_gauss` y solo añade la
eliminación hacia arriba, así que la diferencia entre los dos métodos está en un
único bloque de código.

`expresiones.py` representa a mano una expresión lineal como una constante más un
coeficiente por variable, y es lo que permite despejar sin manipular texto: primero
se calcula la expresión con `Fraction` y solo al final se escribe. `sistemas.py`
usa esa misma pieza para traducir matrices a ecuaciones y para construir el
conjunto solución, de modo que Gauss y Gauss-Jordan comparten la interpretación
entera.

`parser_sistemas.py` queda fuera de esa cadena porque no depende de ningún otro
módulo del proyecto: recibe texto y devuelve una matriz, o lanza `ValueError`. Eso
permitirá reutilizarlo tal cual desde otra interfaz.

`backend/` contiene lógica pura: no usa `input()` ni `print()` y no depende de
ninguna interfaz. `frontend/terminal/` es quien consume el backend y concentra
toda la interacción por consola. La dependencia va siempre en un sentido:

```text
frontend/terminal  →  backend
frontend/web        →  backend
```

Esa separación deja espacio para añadir más adelante otra interfaz bajo
`frontend/` sin tocar la lógica matemática.

La interfaz web sigue el mismo sentido de dependencia para ambos tipos de
entrada:

```text
texto ───────────────→ parser_sistemas.py ─┐
cuadrícula ──────────→ matriz aumentada ────┼→ servicios.py → sistemas.py
                                            └──────────────→ gauss / gauss-jordan
```

`forms.py` valida dimensiones y celdas con las utilidades existentes del parser;
`servicios.py` adapta matrices, pasos y mensajes para los templates, pero no
recalcula operaciones, clasificaciones ni soluciones. `matriz.js` solo genera la
cuadrícula, cambia su visibilidad y atiende los botones de estructura;
`teclado.js` inserta en el campo activo lo que declara cada tecla; `buscador.js`
filtra el registro ya renderizado; `navigation.js` controla la barra lateral; y
`tema.js` guarda el tema claro u oscuro en el almacenamiento local del WebView.

La arquitectura completa de las interfaces queda así:

```text
frontend/terminal
        │
        └──────────────→ backend

frontend/web
        │
        └──────────────→ backend

desktop.py
        ↓
     Waitress (127.0.0.1:<puerto efímero>)
        ↓
     Django WSGI
        ↓
frontend/web
        ↓
     backend
```

El launcher es infraestructura de ejecución y no contiene parser, operaciones
de filas, Gauss, Gauss-Jordan ni interpretación matemática.

## Desarrollo

El flujo de ramas, las convenciones de commits y las reglas para contribuir están
en [CONTRIBUTING.md](CONTRIBUTING.md).
