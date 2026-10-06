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

En la web también se puede escribir una ecuación por línea: un salto de línea
(`\n` o `\r\n`, el que envía el navegador) separa ecuaciones igual que `;`, y
las líneas vacías se ignoran. Estos dos textos son el mismo sistema:

```text
x1 - 6 = -x2
2x1 + x2 = 8
```

```text
x1 - 6 = -x2; 2x1 + x2 = 8
```

Un salto de línea solo separa si la línea anterior ya tiene su `=` y la
siguiente trae el suyo; así una ecuación larga puede seguir en la línea
siguiente (`x1 + x2` y `= 6` en dos líneas siguen siendo una ecuación), como
hasta ahora. Un `;` sin ecuación (`x1 = 2;;`) sigue siendo un error.

Las variables son `x1`, `x2`, `x3`, … con índice desde 1. Se admiten espacios
libres, coeficientes implícitos (`x1` vale `1x1` y `-x2` vale `-1x2`), variables
ausentes (valen cero), enteros, fracciones (`1/2x1`) y decimales (`0.5x1`).

Los términos y las constantes pueden ir en cualquiera de los dos lados del `=`;
no hace falta despejar ni ordenar antes de escribir. PyGebra normaliza cada
ecuación a la forma estándar `a1x1 + … + anxn = b`:

```text
x1 - 6 = -x2       →  x1 + x2 = 6
2x1 + 3 = x2 - 5   →  2x1 - x2 = -8
6 = x1 + x2        →  x1 + x2 = 6
x1 + x1 + x2 = 6   →  2x1 + x2 = 6
```

Las variables quedan a la izquierda y el número a la derecha, sumando los
términos semejantes; si todas las variables estaban a la derecha, se
intercambian los lados. Una ecuación que ya estaba en esa forma produce
exactamente la misma fila que antes. Una ecuación sin variables (`3 = 5`) y las
expresiones no lineales (`x1*x2`, `x1^2`, `1/x1`, `sqrt(x1)`, `sin(x1)`) se
rechazan con un mensaje que explica el motivo.

El ingreso manual pide la cantidad de variables y de ecuaciones, y luego cada
coeficiente y cada término independiente. Ambas formas producen exactamente la
misma matriz aumentada, así que son intercambiables.

Volver al menú, o escribir un sistema con un formato inválido, deja intacta la
matriz activa: solo un sistema creado correctamente la reemplaza.

## Resolución de sistemas en terminal

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
elige dentro, igual que el método en Reducción por filas. La dimensión `n`
no está fijada, así que cada vector se escribe como una fila de
celdas, `u = ( [ ] [ ] [ ] )`, y los botones **+/−** agregan o quitan
componentes (de 1 a 10). No hay campos `x`, `y`, `z` ni sintaxis de listas.

- **Suma** y **resta** operan componente a componente y exigen la misma
  dimensión: `(1, 2, 3) + (4, 5, 6) = (1 + 4, 2 + 5, 3 + 6) = (5, 7, 9)`.
- **Multiplicación por escalar** multiplica cada componente por `k`:
  `3(1, -2, 4) = (3·1, 3·(-2), 3·4) = (3, -6, 12)`.
- **Combinación lineal** pregunta si `b` es combinación lineal de `v1 … vk`
  (de 1 a 6 vectores, con **+/− vector**). No hay un segundo algoritmo de
  eliminación: `x1·v1 + … + xk·vk = b` se escribe como la matriz aumentada
  `[v1 v2 … vk | b]` —cada generador es una columna y `b` la columna
  aumentada— y se resuelve con el Gauss-Jordan de `backend/sistemas.py`. La
  clasificación del sistema decide la respuesta:
  - solución única: **sí**, y se muestran `x1, x2, …` y la igualdad
    `(3, 4) = 3(1, 0) + 4(0, 1)`;
  - soluciones infinitas: **sí**, con la solución general en función de los
    coeficientes libres y una combinación concreta (libres en cero);
  - inconsistente: **no**, porque el sistema asociado no tiene solución.

El procedimiento, plegado bajo «Ver procedimiento», habla el lenguaje del
ejercicio —los coeficientes son las incógnitas `x1, x2, …`—: planteamiento,
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

La herramienta **Conversión de bases** (`/bases/conversion/`) convierte números
entre binario, octal, decimal y hexadecimal: se escribe el número,
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
muestra esa sustitución (`10 → A`, `A = 10`) y va plegado bajo «Ver
procedimiento», antes del resultado. Se admite un punto decimal (`.31` como `0.31`, `5.` como `5`) y un
único `-` al inicio. El signo se conserva y el algoritmo trabaja sobre la
magnitud, así que `-13₁₀` es `-1101₂`: no es complemento a dos. El cero negativo
(`-0`, `-0.0`) se escribe `0`. Los dígitos inválidos para la base elegida, la
entrada vacía y un signo mal colocado se rechazan con un mensaje claro; no se
admiten otras bases.

El núcleo vive en `backend/sistemas_numericos/` y devuelve los pasos como datos
(dividendo, cociente, residuo y símbolo; o dígito, valor, posición, potencia y
aporte), sin HTML. `convertir_a_varias_bases` obtiene el decimal una vez y lo
reparte entre los destinos; `convertir` es su caso de un solo destino. No usa
`bin`, `oct`, `hex` ni `int(texto, base)`: la conversión se construye a mano, y
`tests/test_sistemas_numericos.py` lo comprueba con `ast`. El teclado en
pantalla ofrece el signo −, el punto y los dígitos válidos para la base de origen
(`0 1`, `0`–`7`, `0`–`9` o `0`–`F`) y, al cambiarla, la entrada se revisa al instante y la
casilla de esa base desaparece de «Convertir a» (sin JavaScript se ven las
cuatro casillas); el servidor vuelve a validar al convertir: destinos válidos,
sin repetir, sin la base de origen, al menos uno, y un número de hasta 128
caracteres.

La herramienta **Conversión de números romanos** (`/romanos/conversion/`) tiene
su propio tema, **Numeración romana**, porque no es un sistema posicional de
base n. Se elige la dirección (**Arábigo → romano** o **Romano → arábigo**), se
escribe un número y se obtiene un único resultado, precedido del procedimiento plegado:

- **Arábigo → romano:** el número se separa por órdenes decimales y cada parte
  se escribe con la tabla romana: `1963 = 1000 + 900 + 60 + 3`, con `1000 → M`,
  `900 → CM`, `60 → LX` y `3 → III`, así que `1963 = MCMLXIII`.
- **Romano → arábigo:** se lee de izquierda a derecha reconociendo las restas
  IV, IX, XL, XC, CD y CM: `MCMLXIII = 1000 + 900 + 50 + 10 + 1 + 1 + 1 = 1963`.

Se usa la notación moderna convencional del 1 al 3999, solo con I, V, X, L, C,
D y M; la entrada romana acepta minúsculas. No hay cero, negativos, fracciones
ni barras para millares. Una escritura romana solo se acepta si es la canónica
de su valor: `IIII` se rechaza indicando que 4 se escribe `IV`, y `VV`, `IC` o
`MMMM` también se rechazan con un mensaje claro. El núcleo vive en
`backend/sistemas_numericos/romanos.py`, separado de la conversión de bases.

## Reducción por filas en la interfaz visual

Inicio de PyGebra permite buscar una herramienta o abrir un área y después
un tema (Vectores, Matrices, Bases numéricas); el menú ☰ abre el mismo árbol
en cualquier página. **Álgebra Lineal → Matrices → Reducción por filas**
(`/matrices/reduccion/`) reduce específicamente una matriz aumentada `[A | b]`.
Puede ingresarse como **Sistema de ecuaciones** (el parser lo convierte a
`[A | b]`) o como **Matriz aumentada**. El backend de sistemas conserva la
clasificación y las soluciones. P26.5 reorganiza la herramienta pública sin
añadir matemática nueva; no existe una categoría pública de Sistemas de ecuaciones.
Resolver Ax = b y Matriz inversa siguen siendo herramientas aparte.

Se configura en el propio formulario:

| Opción | Valores | Predeterminado |
| --- | --- | --- |
| Método | Gauss, Gauss-Jordan o Comparar ambos | Gauss-Jordan |
| Tipo de entrada | Sistema de ecuaciones o Matriz aumentada | Sistema de ecuaciones |
| Mostrar | Procedimiento, Clasificación, Columnas pivote, Sistema resultante | Todos activos |

La matriz final y la solución se muestran siempre. Las casillas de Mostrar
esperan plegadas bajo «Opciones de resultado». Tras resolver, la página lee
Entrada → «Ver procedimiento» (plegado: matriz inicial, operaciones por filas,
matriz final, sistema resultante y sustitución regresiva) → Resultado final
(clasificación, solución y columnas pivote), siempre visible y una sola vez;
si «Procedimiento» se desmarca, la matriz final pasa al resultado. Si alguna
ecuación se escribió con términos en ambos lados, el procedimiento empieza por
su forma estándar (`x1 - 6 = -x2 → x1 + x2 = 6`), antes de la matriz inicial;
las que ya estaban normalizadas no repiten ese paso.
«También puedes explorar» ofrece el mismo sistema con el otro método o
comparando, los bloques omitidos y Resolver Ax = b. **Comparar ambos** resuelve
la misma entrada con los dos métodos y pliega cada procedimiento en su propio
sub-bloque; como la clasificación y la solución coinciden, aparecen una sola
vez, en el resultado común.
Las rutas anteriores (`/sistemas/`, `/sistemas/gauss/`, `/sistemas/gauss-jordan/`,
`/sistemas/clasificacion/` y `/sistemas/columnas-pivote/`) redirigen a
`/matrices/reduccion/`: GET usa 301. POST a `/sistemas/` se procesa con la
misma vista (200) y formularios canónicos; POST a los cuatro slugs usa 308,
conservando cuerpo y método. Así también funcionan los clientes históricos
que enviaban POST directamente a `/sistemas/` sin seguir redirecciones.
Se conservan los parámetros GET, incluidas las casillas repetidas; las rutas
de Gauss y Gauss-Jordan sugieren método cuando no se indicó uno explícito.
El botón **Reducir** envía siempre a la ruta canónica.

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
un sistema. Aparece al enfocar una entrada compatible y desaparece al salir
o pulsar Escape. Sin JavaScript permanece oculto; el teclado físico siempre
está disponible. En Sistemas alterna entre ecuaciones y valores numéricos;
las celdas numéricas comparten negativo y fracción. Las expresiones matriciales
añaden paréntesis y traspuesta; las componentes lineales ofrecen x₁…x₆.
Los nombres de símbolos y Romanos no lo activan. En conversión de bases cambia
los dígitos según la base de origen, conservando la conversión a varios destinos.

## Operaciones matriciales y Ax = b

**Operaciones con matrices** (`/matrices/operaciones/`) es la herramienta
general de la categoría Matrices: realiza y combina operaciones con matrices,
vectores y escalares paso a paso. Desde P26.6 las operaciones simples y las
compuestas usan el mismo formulario y el mismo motor de expresiones
(`backend/expresiones_matriciales/`); no hay un modo «sencillo» aparte:

```text
A + B    A - B    2A    AB    Ax    Aᵀ
2A + B   AB - C   A(B + C)   2A - BC   (A + B)ᵀ
```

Expresiones matriciales dejó de ser una herramienta separada (ver
[Compatibilidad](#compatibilidad-de-expresiones-matriciales)).

El usuario define solo los símbolos que va a usar —nombre, tipo, dimensiones y
valores; al abrir hay dos matrices 2×2, A y B— y escribe la expresión. Filas y
columnas van de 1 a 10 por legibilidad; el backend no impone ese límite ni exige
matrices cuadradas. Con JavaScript se agregan, quitan y redimensionan símbolos
sin recargar, las flechas recorren la cuadrícula de cada símbolo y los
controles +/− conservan los valores; sin JavaScript, **Agregar símbolo**,
**Eliminar** y **Aplicar** hacen lo mismo en el servidor. El teclado contextual
existente permite negativos y fracciones.

### Sintaxis

Enteros, fracciones (`1/2`, `-3/4`) y los decimales exactos que ya acepta el
parser del proyecto. Símbolos definidos por el usuario (`A`, `u`, `k`, `A1`).
Operadores `+`, `-`, `*`, paréntesis y la traspuesta. El menos unario aplica al
factor siguiente: `-3B` es `(-3)B`.

La multiplicación implícita equivale a `*` cuando hay una sola lectura:

```text
2A ↔ 2*A    AB ↔ A*B    Au ↔ A*u    A(u + v) ↔ A*(u + v)
```

Si `AB` puede ser el símbolo `AB` o el producto `A*B`, la expresión se rechaza
y hay que escribir `*`. No se adivina.

La **traspuesta** es una operación del árbol (nodo `Traspuesta`), no un
reemplazo de texto. `Aᵀ` y `A^T` son la misma operación; el procedimiento la
escribe siempre como `ᵀ`. Es postfija y afecta solo al factor que la precede:
`ABᵀ` es `A(Bᵀ)`; para trasponer el producto se escribe `(AB)ᵀ`. Se aplica a
matrices con entradas conocidas; para una fila, se define una matriz de 1×n.
`^` no forma potencias: `A^2` y `A^-1` se rechazan sin interpretarlos (la
inversa se calcula en la herramienta Matriz inversa).

Precedencia: paréntesis y traspuesta, menos unario, multiplicación (implícita o
`*`), suma y resta. En cada nivel se agrupa de izquierda a derecha:

```text
A + BC = A + (BC)     A - B - C = (A - B) - C     ABC = (AB)C
```

Una cadena de productos se evalúa en ese orden; no se reordena para ahorrar
cuentas (no hay optimización de la parentización).

Un solo `=` compara dos expresiones, por ejemplo `A(u + v) = Au + Av` o
`(AB)ᵀ = BᵀAᵀ`. No es una operación como `+` o `*`: cada lado se analiza con el
mismo parser. Se rechazan `A = B = C`, `==`, un lado vacío y los demás
operadores relacionales.

### Procedimiento por nodos

Cada nodo del árbol se calcula una vez con `backend/matrices.py` o
`backend/vectores.py` y muestra su propio procedimiento, el mismo del módulo
anterior de Operaciones con matrices:

- **suma, resta y escalar**: la regla por entrada (`cᵢⱼ = aᵢⱼ + bᵢⱼ`,
  `(kA)ᵢⱼ = k · aᵢⱼ`) y una sola cadena `A + B = [A] + [B] = [desarrollo] = [C]`;
- **traspuesta**: `(Aᵀ)ᵢⱼ = Aⱼᵢ`, el cambio de dimensiones (`2×3 → 3×2`) y
  cómo cada fila pasa a ser una columna (`Fila 1 de A → columna 1 de Aᵀ`);
- **AB y Ax**: las lecturas del mismo producto, elegidas en **Opciones del
  procedimiento** → **Cómo mostrar los productos**: **Fila por columna**
  (`cᵢⱼ = filaᵢ(A) · columnaⱼ(B)`; en `Ax`, **Regla fila-vector**), **Por
  columnas** (`AB = [Ab₁ Ab₂ … Abₚ]`, con cada `Abⱼ` como combinación lineal de
  las columnas de A; en `Ax`, **Combinación lineal de columnas**:
  `Ax = x₁a₁ + … + xₙaₙ`) o **Comparar ambos**. Es solo presentación: el
  producto se calcula una vez (los productos `aᵢₖbₖⱼ` se agrupan por entrada y
  por columna) y el resultado no cambia;
- **vectores y escalares**: una línea por componente (`4 + (-3) = 1`).

Los pasos siguen el orden en que se calcularon (hijos primero). En `A(B + C)`
aparecen `B + C` y después `A(B + C)`; en `(A + B)ᵀ`, la suma y después su
traspuesta; en `AB + C`, el producto con la lectura elegida y después la suma.
Cada paso intermedio cierra con su valor, que usa el paso siguiente; el último
no lo repite, porque es el resultado y se muestra una sola vez, en el panel
Resultado, fuera del procedimiento plegado.

Cuando la expresión es un producto o una suma de dos símbolos (`AB`, `A + B`),
las entradas se llaman `cᵢⱼ` y las fórmulas son las del módulo anterior. Dentro
de una expresión mayor se llaman como el paso, `(AB)ᵢⱼ` o
`(A(B + C))ᵢⱼ = filaᵢ(A) · columnaⱼ(B + C)`, para no confundirse con otro
operando. Una subexpresión como operando se escribe entre paréntesis cuando
hace falta: `(B + C)₁₁`, `(A + B)c₁`.

Cada paso ofrece **Calcular solo esta parte**, que evalúa ese nodo por su ruta
estable (`0`, `0.1`, `0.1.0`; en una igualdad, `izq:0.1` o `der:0`). Las rutas
de una expresión sin traspuesta no cambian respecto de las versiones
anteriores; una traspuesta es un nodo más con su propia ruta.

El selector Exacto/Decimal alcanza el resultado, los valores intermedios y las
igualdades de cada procedimiento.

### Tipos, dimensiones e igualdades

Suma y resta: matriz con matriz, vector con vector o escalar con escalar, y
solo si las dimensiones coinciden. Producto: escalar con escalar, vector o
matriz; matriz con matriz; matriz con vector. Traspuesta: solo matrices. No hay
producto punto automático ni producto vector por matriz.

En `Ax` el vector x es conocido y solo se calcula el producto. Buscar x es otra
herramienta, **Resolver Ax = b**, que no cambia.

El error nombra la subexpresión que falla. Si `B + C` no se puede sumar, el
mensaje habla de `B + C`. Si esa suma existe pero `A(B + C)` no se puede
multiplicar, el mensaje habla de ese producto y muestra las dimensiones. Dentro
de una igualdad, además indica si el fallo está en el lado izquierdo o en el
derecho. Una igualdad falsa no es un error: es un resultado.

Con símbolos numéricos, que ambos lados coincidan significa que producen el
mismo objeto para esos valores. No demuestra la identidad para todos los
valores. La comparación usa los `Fraction` calculados, no el texto decimal, y
solo es verdadera o falsa si ambos lados son el mismo tipo y las mismas
dimensiones; si no, el mensaje dice qué es cada lado.

### Tipos simbólicos

Siguen disponibles, sin capacidades nuevas, agrupados como «Simbólicos» en el
selector de tipo. El camino simbólico solo se activa si un símbolo se declaró
como matriz desconocida, vector simbólico o vector lineal. Un nombre sin
definición sigue siendo un error.

Una forma lineal es una constante más un coeficiente exacto por variable, por
ejemplo `3x1 - 2x2 + 5`. Los coeficientes son `Fraction`. Dos textos distintos
con los mismos coeficientes son la misma forma: `x1 + x1` es `2x1` y
`2(x1 + x2) - x1` es `x1 + 2x2`. Una variable que no aparece tiene coeficiente 0.

Solo se conservan la suma, la resta, la negación y el producto por un escalar
numérico. Se rechazan `x1*x2`, `x1^2`, `1/x1`, la traspuesta y llamadas como
`sin(x1)`.

En la misma página se declaran tres objetos, sin adivinar incógnitas:

- **Matriz desconocida.** Nombre, filas y columnas. No tiene celdas.
- **Vector simbólico.** Nombre y cantidad de componentes. `x` con 2 componentes
  es `[x1, x2]`, en ese orden. Esas variables no se evalúan a un número.
- **Vector lineal.** Cada componente se escribe como texto y pasa por el parser
  lineal. No se usa `eval`.

Si la expresión es `Ax = b`, A es la única matriz desconocida, x el vector
simbólico de n componentes y b un vector lineal de m componentes cuyas variables
pertenecen a x, PyGebra determina A comparando coeficientes. No usa Gauss.

`Ax = x1 a1 + … + xn an`. Si b se agrupa como `x1 c1 + … + xn cn`, entonces
`aj = cj` para que la igualdad valga para todos los valores de las variables.
La columna j de A es el vector de coeficientes de la variable j. Después se
reconstruye `Ax` con esa matriz y se comparan los coeficientes exactos; no se
sustituyen valores de prueba.

Un término constante distinto de cero no puede salir de `Ax`. Una variable que
no está en x, como `x3` cuando x es `[x1, x2]`, se rechaza. Las dimensiones se
comprueban antes: A de 3×2 no admite un x de 3 componentes, y `Ax` de 3
componentes no se iguala con un b de 4.

Si A ya es numérica y x es simbólico, la misma igualdad compara los dos vectores
lineales. Coincidir entonces significa la misma expresión para todos los valores
de las variables declaradas, no solo para los números de una matriz concreta.

### Presupuesto de entrada

El presupuesto es el mismo de las operaciones del módulo anterior, aplicado a
símbolos y a la expresión, y se comprueba antes de crear un campo por celda:

| Qué se cuenta | Tope | Por qué |
| --- | ---: | --- |
| Símbolos definidos | 50 | El máximo lógico de operandos (`OPERANDOS_MAXIMOS`). |
| Celdas de todos los símbolos | 900 | `CELDAS_MAXIMAS`, como antes. |
| Campos de estructura y celdas | 990 | Cada símbolo envía nombre, tipo y hasta dos dimensiones además de sus celdas; con los controles fijos (csrf, expresión, cantidad, presentación y el botón) el envío queda dentro de los 1000 campos de Django (`CAMPOS_MAXIMOS`). |
| Operandos de la expresión | 50 | Cada aparición de un símbolo o de un número cuenta: `AAAA` usa cuatro veces A. |
| Operaciones de la expresión | 49 | Las de una operación de 50 operandos; acota también las cadenas de signos y traspuestas (`Aᵀᵀᵀ…`, `---A`). |
| Entradas de los operandos | 900 | Cada aparición cuenta todas sus entradas: repetir una matriz 10×10 diez veces no cabe. |

El tope histórico de 8 símbolos de Expresiones matriciales desapareció. Lo que
el módulo anterior admitía sigue cabiendo con 22 matrices o menos (900 celdas);
con 50 matrices caben hasta 790 celdas, porque 200 campos son de estructura.
Solo se pierden los envíos extremos de 23 o más matrices que, entre todas,
pasan de `990 − 4 × cantidad` celdas (por ejemplo, 36 matrices de 5×5). Para
recuperarlos habría que subir `DATA_UPLOAD_MAX_NUMBER_FIELDS`, que P26.2 fijó
como límite estructural. Si una estructura no cabe, se dibujan los mismos
símbolos con dimensiones iniciales y un mensaje lo explica; con JavaScript,
agregar o redimensionar no se aplica y el mensaje aparece al instante. La
seguridad numérica común (literales acotados, `BITS_MAXIMOS`) no cambia.

### Arquitectura

```text
texto → ¿un solo =?
  no → lexer → parser → AST → evaluador → primitivas existentes
  sí → cada lado por ese mismo camino
        numérico → comparación de los dos valores
        Ax simbólico → coeficientes de formas lineales → matriz A
```

Cada nodo guarda operación, hijos, texto y su ruta. La evaluación recorre cada
árbol de abajo hacia arriba y llama a `resolver_operacion_matrices` (suma,
resta, escalar, traspuesta, `AB` y `Ax`) o a `backend/vectores.py`; no hay otra
suma, otro producto ni otra traspuesta. `servicios_expresiones.py` arma un paso
por nodo y delega la escritura en `servicios_matrices.py`
(`presentar_producto`, `presentar_por_entrada`), que convierte los datos exactos
ya calculados en textos sin volver a calcular. `forms_expresiones.py` valida la
estructura, el presupuesto y los números con el parser común
(`FormularioCeldas`).

### Compatibilidad de Expresiones matriciales

`/matrices/expresiones/` ya no es una herramienta: un GET redirige con 301 a
`/matrices/operaciones/` conservando la consulta, y un POST usa 308 para que el
navegador reenvíe el mismo cuerpo, que el formulario unificado entiende tal cual
(es el de expresiones; un envío sin la opción de productos usa fila por
columna). No hay una segunda tarjeta en el catálogo, y las búsquedas de
«expresiones matriciales», «expresión», «2A» o «AB» llevan a Operaciones con
matrices.

El contrato POST interno anterior de `/matrices/operaciones/` (`operacion`,
`filas`, `columnas`, `columnas_b`, `celda_A_i_j`…) se retiró: mantenerlo exigía
inferir la estructura de las celdas y sostener un segundo contrato sin otros
clientes que las pruebas y el smoke de Windows, que ahora usan el formulario de
símbolos. Los GET y los enlaces siguen funcionando.

### Límites

No hay inversa, determinante ni potencias dentro de la expresión numérica. En
el camino simbólico tampoco hay dos matrices desconocidas, `AX = B`, `XA = B`,
inversas o determinantes simbólicos, polinomios, división por variables ni un
sistema algebraico general. Un nombre que no esté definido sigue siendo un
error, no una incógnita.

### Resolver Ax = b

En `Ax` el vector x es conocido y solo se calcula el producto. Buscar x es
otra herramienta de la categoría Matrices: **Resolver Ax = b**
(`/matrices/ecuaciones/`). Allí A (m×n) y b son conocidos, x es la incógnita y
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
`matrices.py`. El método se elige como en Reducción por filas (Gauss,
Gauss-Jordan, predeterminado, o Comparar ambos, que muestra el resultado una
sola vez y los dos procedimientos plegados). El procedimiento va plegado
primero y el resultado después, siempre visible:

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
eliminación con los mismos bloques de Reducción por filas: operaciones por
filas, matriz escalonada o reducida con sus pivotes, columnas pivote, sistema
resultante y sustitución regresiva. La comprobación `A · x = b` y la
interpretación van en sus propios bloques plegados después del resultado.
`EcuacionMatricialForm`
(`forms_ecuaciones.py`) comparte con Operaciones con matrices y Matriz inversa la base `FormularioCeldas`
—celdas, parser y comprobaciones del POST— y exige que b tenga exactamente
una componente por fila de A; x nunca viaja en el POST. Con JavaScript los
controles +/− regeneran A, x y b; sin JavaScript, **Aplicar** redibuja la
misma estructura.

Para las decisiones de presentación y accesibilidad, consulta [Interfaz](interfaz.md).
La reutilización del cálculo se explica en [Algoritmos](algoritmos.md).

## Matriz inversa

**Matriz inversa** (`/matrices/inversa/`) recibe una matriz cuadrada A, de 1×1
a 10×10, y calcula su inversa exacta. El método se elige en el formulario:

- **Gauss-Jordan** (predeterminado, cualquier tamaño): coloca la identidad
  junto a A, aplica operaciones por filas a `[A | I]` y, si el lado izquierdo
  llega a la identidad, el derecho es `A⁻¹`.
- **Método para matrices 2×2** (solo si A es 2×2): calcula `ad − bc` y, si no
  es 0, intercambia a y d, cambia el signo de b y c y multiplica por
  `1/(ad − bc)`.

Si A no tiene inversa, el resultado lo dice con una explicación breve según el
método. Un cálculo con Gauss-Jordan que se estima largo pide confirmación antes
de ejecutarse. Los detalles, los ejemplos y la API están en
[Matriz inversa](matriz-inversa.md).

## Visualización de resultados en PyGebra

Sistemas, Vectores, Operaciones con matrices y Ax=b permiten alternar **Exacto / Decimal**
después de resolver. El máximo de decimales puede ser 2, 4 (predeterminado),
6 u 8. La preferencia se conserva localmente entre herramientas compatibles.
`1/2` se ve como `0.5` y `1/3` como `0.3333` con cuatro decimales; `4` sigue
siendo `4`. Se indica `≈` en expresiones redondeadas y una nota de aproximación
para matrices o grupos. La precisión afecta también a todo el procedimiento.

No se recalcula: la fuente de verdad sigue siendo `Fraction`, con aritmética
exacta en Python. Sin JavaScript, el resultado exacto y sus pasos permanecen
disponibles. Conversión de bases queda fuera de este modo de presentación.
