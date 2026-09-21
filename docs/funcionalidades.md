# Funcionalidades y uso

[Índice de documentación](README.md) · [Portada](../README.md)

Las herramientas visuales se usan desde Django o desde la aplicación Windows.
La terminal conserva su menú de matrices y sistemas; no incluye todos los módulos visuales.

## Terminal

Permite generar matrices aleatorias, crearlas manualmente, modificar o consultar
elementos y mostrar las columnas alineadas. Inicia con `uv run python main.py`.

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

Las columnas pivote se numeran desde 1 (`C1`, `C2`, …) y no incluyen la
columna de términos independientes. Se muestran en web, escritorio y terminal.

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

En **Operaciones con vectores** (`/vectores/operaciones/`) la operación se
elige dentro, igual que el método en Resolver un sistema. La dimensión `n`
no está fijada, así que cada vector se escribe como una fila de
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

El procedimiento, plegado bajo «Ver procedimiento», habla el lenguaje del
ejercicio —coeficientes `c1, c2, …`, no variables `x1, x2, …`—: planteamiento,
sistema equivalente, matriz aumentada, operaciones por filas, matriz reducida
y lectura de la matriz; la conclusión y los coeficientes solo aparecen en el
resultado. En suma, resta y escalar el desarrollo es una sola cadena,
`u + v = (1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)`.
Todo se calcula con `fractions.Fraction`: `(1/2, 2/3) + (1/2, 1/3) = (1, 1)`.

El núcleo vive en `backend/vectores.py` (listas, ciclos y `Fraction`, sin
librerías externas). El formulario reconstruye la estructura esperada
(dimensión y cantidad de vectores) y la compara con lo recibido, así que un
POST con celdas de más, de menos o con otros nombres se rechaza; las
dimensiones incompatibles se detectan antes de intentar resolver.

## Sistemas numéricos

La herramienta **Conversión de bases** (`/bases/conversion/`) convierte enteros
no negativos entre binario, octal, decimal y hexadecimal: se escribe el número,
se elige una única base de origen y, bajo **Convertir a**, se marcan una, varias
o todas las demás bases (la de origen no se ofrece como destino y hace falta al
menos una). Solo hay dos algoritmos, y cualquier par de bases se resuelve con
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
  intermedio a la vista. `1010₂ → 10₁₀ → A₁₆`.

Con varios destinos el procedimiento no se repite: cada etapa aparece una sola
vez y solo se calcula lo pedido. Si el origen no es decimal, la expansión
posicional es la etapa compartida y de su valor salen las divisiones de cada
base marcada; si se marcó decimal, su resultado es ese valor intermedio y no
genera una segunda etapa. Si el origen ya es decimal, no hay etapa intermedia.
`17₈ → 15₁₀ → 1111₂ y F₁₆`: una expansión, dos divisiones y tres resultados
(`1111₂`, `15₁₀`, `F₁₆`) si se marcaron las tres bases.

En hexadecimal los residuos y dígitos `10`–`15` se escriben `A`–`F`; la entrada
acepta minúsculas y el resultado se normaliza a mayúsculas. El procedimiento
muestra esa sustitución (`10 → A`, `A = 10`) y siempre queda visible junto al
resultado. Los dígitos inválidos para la base elegida, la entrada vacía y los
números negativos se rechazan con un mensaje claro; no se admiten fracciones ni
otras bases.

El núcleo vive en `backend/sistemas_numericos/` y devuelve los pasos como datos
(dividendo, cociente, residuo y símbolo; o dígito, valor, posición, potencia y
aporte), sin HTML. `convertir_a_varias_bases` obtiene el decimal una vez y lo
reparte entre los destinos; `convertir` es su caso de un solo destino. No usa
`bin`, `oct`, `hex` ni `int(texto, base)`: la conversión se construye a mano, y
`tests/test_sistemas_numericos.py` lo comprueba con `ast`. El teclado en
pantalla solo ofrece los dígitos válidos para la base de origen (`0 1`, `0`–`7`,
`0`–`9` o `0`–`F`) y, al cambiarla, la entrada se revisa al instante y la
casilla de esa base desaparece de «Convertir a» (sin JavaScript se ven las
cuatro casillas); el servidor vuelve a validar al convertir: destinos válidos,
sin repetir, sin la base de origen, al menos uno, y un número de hasta 128
caracteres.

## Sistemas en la interfaz visual

Inicio permite buscar una herramienta o entrar en un tema (Sistemas de
ecuaciones, Vectores, Matrices; las demás áreas bajo «Ver más temas»); el
menú ☰ abre el mismo árbol en cualquier página. Dentro de **Álgebra Lineal →
Sistemas de ecuaciones** hay una sola herramienta, **Resolver un sistema**
(`/sistemas/`), que se configura en el propio formulario:

| Opción | Valores | Predeterminado |
| --- | --- | --- |
| Método | Gauss, Gauss-Jordan o Comparar ambos | Gauss-Jordan |
| Mostrar | Procedimiento, Clasificación, Columnas pivote, Sistema resultante | Todos activos |

La matriz final y la solución se muestran siempre. Las casillas de Mostrar
esperan plegadas bajo «Opciones de resultado». Tras resolver, la página lee
Entrada → «Ver procedimiento» (plegado: matriz inicial, operaciones por
filas, matriz final, sistema resultante y sustitución regresiva) → Resultado
final (clasificación, solución y columnas pivote), siempre visible y una sola
vez; si «Procedimiento» se desmarca, la matriz final pasa al resultado.
«También puedes explorar» ofrece el mismo sistema con el otro método o
comparando, los bloques omitidos y Resolver Ax = b. **Comparar ambos** resuelve
la misma entrada con los dos métodos y pliega cada procedimiento en su propio
sub-bloque; como la clasificación y la solución coinciden, aparecen una sola
vez, en el resultado común.
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

El **teclado matemático** único de cada herramienta se adapta al campo activo y muestra notación
matemática (`x₁`, `−`, `a⁄b`) e inserta la sintaxis que entiende el parser
(`x1`, `-`, `/`), de modo que nadie necesita conocer esa sintaxis para escribir
un sistema. Va plegado bajo «Teclado matemático», solo aparece con JavaScript
y solo contiene teclas con una inserción real. En Sistemas alterna entre
ecuaciones y valores numéricos; Matrices, Vectores y Ax = b comparten las
teclas de negativo y fracción. En conversión de bases cambia los dígitos
según la base de origen, conservando la conversión a varios destinos.

## Operaciones matriciales y Ax = b

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
una sola vez; cada método (un sub-bloque plegado al comparar) muestra su
procedimiento con la igualdad completa de
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
`servicios_matrices.py` adapta los datos a presentación. El procedimiento va
plegado antes del resultado: la regla por entrada y una sola cadena
`A + B = [A] + [B] = [desarrollo] = [C]`; la traspuesta explica el intercambio
de filas/columnas y de dimensiones. La matriz obtenida se presenta una vez,
en el panel Resultado.
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
sola vez y los dos procedimientos plegados). El procedimiento va plegado y el
resultado, debajo, siempre visible:

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
del sistema. «Ver procedimiento» muestra la cadena de equivalencias —ecuación
matricial, ecuación vectorial con las columnas de A, sistema equivalente
(`ecuaciones_de_matriz`, con `n` incógnitas) y matriz aumentada— y después la
eliminación con los mismos bloques de Resolver un sistema: operaciones por
filas, matriz escalonada o reducida con sus pivotes, columnas pivote, sistema
resultante y sustitución regresiva. La comprobación `A · x = b` y la
interpretación van en sus propios bloques plegados después del resultado. `EcuacionMatricialForm`
(`forms_ecuaciones.py`) comparte con `MatricesForm` la base `FormularioCeldas`
—celdas, parser y comprobaciones del POST— y exige que b tenga exactamente
una componente por fila de A; x nunca viaja en el POST. Con JavaScript los
controles +/− regeneran A, x y b; sin JavaScript, **Aplicar** redibuja la
misma estructura.

Para las decisiones de presentación y accesibilidad, consulta [Interfaz](interfaz.md).
La reutilización del cálculo se explica en [Algoritmos](algoritmos.md).
