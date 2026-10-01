# Matriz inversa

[Índice de documentación](README.md) · [Matrices aumentadas por bloques](matrices-aumentadas.md) ·
[Presupuesto computacional](presupuesto-computacional.md)

P26.4 añade **Matriz inversa** (`/matrices/inversa/`), la cuarta herramienta
de Matrices en ese incremento. Desde P26.5 comparte el catálogo de cinco herramientas
con Reducción por filas. Recibe una matriz cuadrada A y calcula su inversa con uno de dos
métodos: **Gauss-Jordan**, para cualquier tamaño, o el **método para matrices
2×2**, solo cuando A es 2×2. Sigue el orden de todas las herramientas: entrada,
«Ver procedimiento» plegado y el resultado al final. Todo es exacto, con
`Fraction`, y el formato Exacto / Decimal funciona como en las demás.

P26.8 añade la opción **Verificar el resultado**, desmarcada de forma
predeterminada. Si se selecciona y A tiene inversa, comprueba exactamente
`A·A⁻¹ = I` y `A⁻¹·A = I` usando la inversa que acaba de calcularse y el
backend de producto de Operaciones con matrices. La inversa se calcula una
sola vez y la verificación queda dentro del procedimiento, antes del resultado.

P26.9 completa las propiedades y la aplicación estudiadas: invertir nuevamente,
trasponer, comprobar la inversa de un producto y aplicar `x = A⁻¹b`.
**Aplicaciones y propiedades** es una sección secundaria plegable con radios:
solo una función adicional puede estar activa. No hay expresión libre ni
combinaciones entre funciones. «Verificar el resultado» conserva exclusivamente
las dos comprobaciones de P26.8 y puede coexistir con cualquier función.

La interfaz no pide saber de antemano qué es `[A | I]`, `A⁻¹`, `ad − bc` o un
determinante. El formulario sirve para elegir qué hacer, y el procedimiento
enseña cómo se hace.

## Ruta y navegación

| Dato | Valor |
| --- | --- |
| Ruta | `/matrices/inversa/` (`calculadora:matriz-inversa`) |
| Catálogo | `MATRIZ_INVERSA`, id `matriz-inversa`, en Álgebra Lineal → Matrices, después de Resolver Ax = b |
| Descripción | «Calcula la inversa de una matriz cuadrada y muestra el procedimiento paso a paso.» |
| Relacionadas | Operaciones con matrices y Resolver Ax = b, tras calcular |

Inicio, menú, migas y buscador salen del catálogo, como en el resto de las
herramientas. El buscador la encuentra por «inversa», «invertible», «no
invertible», «matriz singular», «identidad», «matriz cuadrada», «A⁻¹», «A^-1»
o «2x2». Sus palabras clave evitan «gauss» y «pivote» a propósito: esas
búsquedas siguen llevando solo a Reducción por filas. El catálogo y los
selectores de método no muestran fórmulas.

## Entrada

`InversaForm` (`forms_inversa.py`) hereda de `FormularioCeldas`, igual que
Operaciones con matrices y Resolver Ax = b. Reutiliza las celdas
`celda_A_i_j`, el parser común y el contrato HTTP estricto: se rechazan celdas
de más o de menos, campos ajenos o repetidos. Como A es cuadrada, la estructura
es un solo control, **Filas y columnas**, de 1 a 10 (`DIMENSION_MAXIMA`; no se
amplía en este incremento). `inversa.js` regenera la cuadrícula con las mismas
plantillas inertes que el servidor y conserva lo escrito. Sin JavaScript,
**Aplicar** redibuja la estructura.

El selector de método solo aparece cuando A es **2×2**: **Gauss-Jordan**,
predeterminado, o **Método para matrices 2×2**. En los demás tamaños no hay
decisión que tomar y el servidor usa `metodo=gauss_jordan` automáticamente.

- Al pasar de 2×2 a otro tamaño, `inversa.js` retira el selector y normaliza a
  Gauss-Jordan. Al volver a 2×2 reaparece con Gauss-Jordan seleccionado;
- sin JavaScript, **Aplicar** hace el mismo cambio y conserva las celdas;
- un POST manipulado con `metodo=directo_2x2` y otro tamaño se rechaza con
  «El método para matrices 2×2 solo se puede usar cuando A es 2×2.», y el
  backend lo rechaza también.

**Verificar el resultado** es un `BooleanField` opcional (`verificar`) con
label explícito y ayuda asociada: «Comprueba que A·A⁻¹ y A⁻¹·A producen la
matriz identidad.». Su estado forma parte de la entrada limpia junto con
`a` y `metodo`, y del contrato HTTP estricto. Sin marcarlo, el cálculo y la
presentación conservan el comportamiento anterior. **Aplicar**, **Cancelar**
y **Continuar** conservan la opción, también sin JavaScript.

### Una función adicional

| Opción | Identificador | Entrada adicional | Resultado |
| --- | --- | --- | --- |
| Sin operación adicional | `ninguna` | — | `A⁻¹` |
| Invertir nuevamente | `inversa_inversa` | — | `(A⁻¹)⁻¹ = A` |
| Traspuesta | `traspuesta` | — | `(Aᵀ)⁻¹ = (A⁻¹)ᵀ` |
| Producto con otra matriz | `producto` | B, n×n | `(AB)⁻¹ = B⁻¹A⁻¹` |
| Aplicar a un vector | `vector` | b, n componentes | `x = A⁻¹b` |

La opción predeterminada es **Sin operación adicional**, con la sección cerrada.
Una opción activa abre la sección al volver a renderizar. B y b aparecen cerca
de la opción elegida y heredan el orden de A, sin controles propios de tamaño.
JavaScript conserva localmente sus celdas al cambiar temporalmente de función,
pero retira sus controles del formulario cuando ya no corresponden.

**Aplicar** conserva A, los datos adicionales que corresponden a la función,
la selección, verificar y el método cuando sigue siendo válido, sin calcular.
Sin JavaScript se elige la función y se pulsa **Aplicar** para dibujar B o b.
El contrato de cálculo exige exactamente las celdas activas: B es obligatoria
en producto y b en vector; rechaza campos ajenos, identificadores desconocidos
y valores repetidos que intenten combinar varias funciones.

### Propiedades y aplicación

Todas reciben la A⁻¹ ya calculada. Cada inversión adicional usa el mismo
método; con el método directo, también B⁻¹ y (AB)⁻¹ se calculan por la regla 2×2.

- **Invertir nuevamente** invierte la A⁻¹ recibida y compara exactamente la
  matriz obtenida con A; no reconstruye A a partir de la identidad.
- **Traspuesta** calcula Aᵀ, invierte Aᵀ y traspone la A⁻¹ recibida. Muestra
  ambas matrices antes de compararlas exactamente.
- **Producto con otra matriz** calcula B⁻¹, AB, (AB)⁻¹ y B⁻¹A⁻¹. El orden
  de los factores se conserva; ambos lados se calculan, sin asumir la propiedad.
- **Aplicar a un vector** explica `Ax = b → A⁻¹Ax = A⁻¹b → Ix = A⁻¹b →
  x = A⁻¹b`, calcula A⁻¹b y comprueba Ax = b exactamente. Usa el motor
  matriz-vector; no llama al solver ni reduce [A | b]. Esta aplicación de la
  inversa mantiene independiente la herramienta **Resolver Ax = b**.

## Método 1: Gauss-Jordan sobre `[A | I]`

`backend/matriz_inversa.inversa_gauss_jordan(a)` compone las primitivas de
P26.3; no hay un segundo Gauss-Jordan:

1. valida que A sea cuadrada (`validar_matriz_cuadrada`);
2. construye `I_n` con `matriz_identidad(n)`;
3. forma `[A | I]` con `aumentar_matrices(a, identidad)`;
4. la reduce con `aplicar_gauss_jordan(aumentada, columnas_pivote=n)`: los
   pivotes solo se buscan en A, pero cada operación transforma la fila completa;
5. separa los bloques con `separar_bloques(reducida, n)`;
6. compara exactamente el bloque izquierdo con `I_n`.

Si la izquierda es la identidad, la derecha es `A⁻¹`. Si no, A no tiene
inversa. No se calculan determinantes. Con A cuadrada, llegar a `I_n` equivale
a encontrar n pivotes; la comparación con la identidad es la evidencia que se
muestra.

Devuelve `metodo`, `orden`, `matriz` (A exacta), `aumentada` (`[A | I]`),
`pasos` y `pivotes` del motor, `reducida`, sus bloques `izquierda` y
`derecha`, `invertible` e `inversa` (el bloque derecho o `None`).

El procedimiento tiene tres etapas cortas:

1. **Colocar la identidad junto a A**: qué es I y la matriz `[A | I]`.
2. **Operaciones por filas**: los pasos que registró el motor, con
   `modules/sistemas/_pasos.html`. `resultado.columnas_izquierda = n` dibuja el
   separador antes de la columna n + 1 en cada matriz: la inicial, antes y
   después de cada paso y la final. No hay otra lógica de «última columna».
3. **Matriz final**: si se llegó a `[I | A⁻¹]`, el bloque derecho es la
   inversa; si no, qué filas del lado izquierdo quedaron con solo ceros.

Esta etapa calcula únicamente A⁻¹; las propiedades y la aplicación se explican
después, cuando se solicitaron.

## Método 2: la regla para matrices 2×2

`inversa_metodo_2x2(a)` aplica el teorema que enseña el curso. Para

```text
A = [a  b]
    [c  d]
```

calcula `ad − bc` con `multiplicar_exacto` y `restar_exacto`. Si vale 0, A no
tiene inversa. Si no:

```text
A⁻¹ = 1/(ad − bc) · [ d  −b]
                    [−c   a]
```

El factor se obtiene con `dividir_exacto` y cada entrada se multiplica con
`multiplicar_exacto`. Devuelve `entradas` (a, b, c y d), `ad`, `bc`,
`ad_menos_bc`, la matriz `intercambiada` `[[d, −b], [−c, a]]`, el `factor`,
`invertible` e `inversa`. Es un segundo método de verdad: no llama a
Gauss-Jordan (una prueba lo sustituye por un error y el método sigue
funcionando).

El procedimiento enseña la regla por etapas: las entradas con letras y con los
números de A, la regla con letras, `ad − bc` con la sustitución numérica
(`ad − bc = 3·6 − 4·5 = 18 − 20 = -2`), el intercambio de a y d con el cambio
de signo de b y c, y la multiplicación por `1/(ad − bc)` entrada por entrada.
La fórmula aparece aquí, dentro del procedimiento, y nunca en el selector.

### Por qué solo 2×2

Intercambiar a y d y cambiar el signo de b y c es exactamente cómo se ve la
fórmula general de la inversa en el caso 2×2. Para n > 2, esa fórmula necesita
cofactores y determinantes de submatrices, que PyGebra todavía no tiene y que
este incremento no introduce. Gauss-Jordan ya cubre cualquier tamaño, así que
el método directo queda como lo que enseña el curso: una regla propia de las
matrices 2×2.

## Matrices sin inversa

El mensaje principal es siempre «La matriz no tiene inversa.». Debajo va una
explicación breve según el método:

| Método | Explicación en el resultado | En el procedimiento |
| --- | --- | --- |
| Gauss-Jordan | «Con Gauss-Jordan, el lado izquierdo no pudo convertirse en la matriz identidad: A es una matriz no invertible.» | Qué filas del lado izquierdo quedaron con solo ceros. |
| 2×2 | «Como ad − bc = 0, A es una matriz no invertible.» | La sustitución que da 0 y por qué la regla no se puede aplicar. |

No se usan términos como rango, conteo de pivotes o excepciones. Con
`[[1, 2], [2, 4]]`, ambos métodos concluyen que no hay inversa; las pruebas
comprueban que los dos métodos coinciden también en 400 matrices 2×2
aleatorias.

Si se pidió verificar, el procedimiento indica «No se puede realizar la
verificación porque A no tiene inversa.». No se construyen productos ni una
verificación falsa, y esta situación conserva el resultado normal; no es un
error.

Las funciones adicionales necesitan A invertible. Si A es singular, se conserva
el resultado principal anterior y no se continúa con ellas. En la aplicación a
b, solo se afirma que no puede usarse `x = A⁻¹b`; no se concluye si el sistema
tiene ninguna o infinitas soluciones. Si únicamente B es singular, el producto
se detiene tras calcular B⁻¹ y explica que la propiedad no puede aplicarse
porque B no tiene inversa. Son condiciones matemáticas válidas, sin alerta roja.

## Verificación opcional

`backend/matriz_inversa.verificar_inversa(a, inversa)` es una función pura
común a los dos métodos. Recibe A y la A⁻¹ ya obtenida, valida que ambas sean
cuadradas del mismo orden y construye `I_n` con `matriz_identidad(n)`. Después
llama exactamente dos veces a
`backend.matrices.resolver_operacion_matrices("producto", ...)`, primero
con A y A⁻¹ y después con A⁻¹ y A. Reutiliza así el producto matricial
existente, sin un segundo motor, sin pasar por otro formulario ni hacer una
petición HTTP a `/matrices/operaciones/`.

Compara cada matriz obtenida exactamente con I. Los datos son enteros o
`Fraction`: no se usan floats, tolerancias ni redondeos. La función devuelve:

```python
{
    "identidad": ...,
    "a_por_inversa": ...,
    "inversa_por_a": ...,
    "a_por_inversa_es_identidad": ...,
    "inversa_por_a_es_identidad": ...,
    "verificada": ...,
}
```

Las tres primeras claves contienen matrices exactas; las dos siguientes
indican el resultado de cada comparación, y `verificada` requiere que ambas
sean verdaderas. Las entradas no se modifican. Las matrices inválidas o
incompatibles se rechazan mediante `ValueError` con un mensaje legible.

La capa web llama una sola vez a `calcular_inversa(a, metodo)`. Solo cuando
`verificar` es verdadero y `invertible` es verdadero pasa esa misma A⁻¹ a
`verificar_inversa`; no vuelve a llamar a ningún método de inversión. Incluye
`verificar_solicitado` y `verificacion` en los datos para las plantillas.

Dentro de «Ver procedimiento», después de las etapas del método elegido,
el encabezado semántico **Verificación** separa dos comprobaciones visibles:
`A·A⁻¹ = matriz obtenida = I` y `A⁻¹·A = matriz obtenida = I`. Las matrices
conservan sus `aria-label`; la comparación se comunica con texto. No se
despliegan todos los productos fila por columna. Si ambas coinciden, se
indica «Ambos productos son la matriz identidad.». Si alguna no coincide, se
muestran igualmente los productos reales y se identifica cuál no coincide,
sin afirmar que la verificación fue correcta.

## Resultado y Exacto / Decimal

`servicios_inversa.calcular_inversa_web` coordina una llamada a
`calcular_inversa(a, metodo)`, la verificación opcional con la inversa obtenida
y el formato de los datos exactos. El resultado va al
final, una sola vez: la matriz de la función elegida en la tabla anterior,
el vector columna x o la explicación de por qué no puede aplicarse. El valor
matricial común de cada propiedad aparece una vez en ese panel. A⁻¹ y los
intermedios necesarios quedan en etapas dentro del procedimiento.
La palabra «Resultado» no aparece dentro del procedimiento. La
cadena del método 2×2 termina en la matriz obtenida, como las cadenas de
Operaciones con matrices; la matriz final de Gauss-Jordan es `[I | A⁻¹]`.

`#resultado` va envuelto en `{% numeric_results %}` y la página carga
`numeros.js`. Por ejemplo, la inversa de la matriz 3×3 del profesor muestra
`-9/2`, `3/2` y `1/2` como `-4.5`, `1.5` y `0.5` sin recalcular. El backend
nunca pasa a `float`.

El bloque de verificación vive en el mismo `{% numeric_results %}` que el
procedimiento y el resultado. Cambiar entre Exacto y Decimal solo cambia la
presentación: no recalcula la inversa ni los productos de verificación.
También incluye B⁻¹, AB, (AB)⁻¹, B⁻¹A⁻¹, Aᵀ, (Aᵀ)⁻¹,
(A⁻¹)ᵀ, x y Ax. Las comparaciones se hacen sobre los valores exactos,
antes de formatearlos.

## Ejemplos del profesor

| A | Método | Resultado | Verificación seleccionada |
| --- | --- | --- | --- |
| `[[3, 4], [5, 6]]` | Gauss-Jordan y 2×2 | `A⁻¹ = [[-3, 2], [5/2, -3/2]]` | Ambos productos son exactamente `[[1, 0], [0, 1]]`. |
| `[[0, 1, 2], [1, 0, 3], [4, -3, 8]]` | Gauss-Jordan (empieza con `F1 <-> F2`) | `A⁻¹ = [[-9/2, 7, -3/2], [-2, 4, -1], [3/2, -2, 1/2]]` | Ambos productos son exactamente `[[1, 0, 0], [0, 1, 0], [0, 0, 1]]`. |
| `[[1, 2], [2, 4]]` | ambos | La matriz no tiene inversa. | No se ejecutan productos. |
| `[[4]]` | Gauss-Jordan automático, sin selector | `A⁻¹ = [[1/4]]` | `[[4]]·[[1/4]] = [[1]]` y `[[1/4]]·[[4]] = [[1]]`. |

Con A = `[[3, 4], [5, 6]]` y b = `[3, 7]`, la aplicación devuelve
exactamente **x = `[5, -3]`** como vector columna. La comprobación da
Ax = `[3, 7]` = b por ambos métodos 2×2.

## Presupuesto y confirmación

Antes de ejecutar cualquier inversión, `estimar_inversa_web` modela el cálculo
completo con P26.2. Cada inversión por Gauss-Jordan usa

```python
estimar_gauss_jordan(n, 2 * n, columnas_pivote=n, perfil=perfil_numerico(a))
```

sin ejecutar matrices intermedias. `estimar_producto` modela los productos y
`combinar_estimaciones` suma todas las partes; `categoria` decide sobre el total:

| Función | Inversiones | Productos adicionales |
| --- | --- | --- |
| Ninguna | 1 | — |
| Invertir nuevamente | 2 | — |
| Traspuesta | 2 | Traspuestas de costo pequeño |
| Producto | 3: A, B, AB | AB y B⁻¹A⁻¹ |
| Vector | 1 | A⁻¹b y Ax, ambos n×n por n×1 |

Verificar añade a cualquiera **dos productos n×n**. El perfil de A y, cuando
corresponde, B o b se conoce antes del cálculo. Los perfiles de inversas y
productos intermedios se aproximan de forma conservadora a partir del orden
y los bits conocidos; no se invierten ni multiplican matrices para estimar.
La regla directa 2×2 tiene una cota pequeña de 14 operaciones y 24 celdas por
inversión, sin modelarla como Gauss-Jordan. Las dos traspuestas conservan
2n² celdas; el perfil de Ax parte del perfil aproximado de x obtenido en
la primera multiplicación. No cambia la calibración, categorías ni umbrales de P26.2.

- **Normal o perceptible**: se calcula directamente.
- **Pesada o muy pesada**: no se calcula. Aparece un aviso dentro del
  formulario, arriba de la matriz, en tonos neutros con acento verde (no es
  una alerta roja):

  > **Antes de calcular**
  >
  > La matriz es válida. Esta operación puede tardar varios segundos porque la
  > matriz requiere un procedimiento largo.
  >
  > Tiempo estimado: entre 1 y 11 segundos.
  >
  > ¿Quieres continuar? [Cancelar] [Continuar]

Con una estimación muy pesada el mensaje dice «puede tardar bastante porque la
matriz requiere un procedimiento muy largo». El tiempo sale de
`intervalo_segundos`, redondeado a segundos (o a minutos desde un minuto y
medio). No se muestran complejidad, bits, operaciones ni celdas.

Como el aviso vive dentro del formulario, A, B/b, el método, la función y la
opción de verificación se conservan:

- **Cancelar** envía `ajustar`, igual que Aplicar: redibuja sin calcular.
- **Continuar** envía `confirmacion` con una firma HMAC (`salted_hmac` con
  SHA-256 y la clave de Django) del método, los valores exactos de A, el
  booleano `verificar`, la función adicional y B o b cuando corresponden.
  `confirmacion_pendiente` recalcula esa firma y la compara con
  `constant_time_compare`. Con la firma correcta se calcula sin volver a
  preguntar, así que no hay bucle ni segunda confirmación al llegar a B⁻¹ o
  (AB)⁻¹. Cambiar A, B, b, método, función o `verificar`, o inventar la firma,
  invalida la autorización anterior y vuelve a pedirla si el total es pesado. Una
  firma concedida con `verificar=False` no autoriza `verificar=True`, ni a la
  inversa. La misma matriz escrita de otra
  forma (`2/2` en lugar de `1`) es la misma entrada.
- Es el servidor quien exige la confirmación; JavaScript solo oculta un aviso
  que dejó de corresponder cuando el usuario edita la matriz, el método o la
  opción de verificación.

La regla 2×2 hace unas pocas operaciones y nunca pide confirmación.

Con las referencias actuales, una 9×9 de enteros queda como perceptible y una
10×10 como pesada (referencia de 3,6 s; intervalo de 1,2 a 10,9 s). En el
equipo de desarrollo, el POST completo midió 1,7 s para 9×9 y 2,7 s para
10×10, dentro del intervalo; desde 6×6 la referencia queda entre un 25 y un
35 % por encima de lo medido. Este incremento no cambia referencias, umbrales
ni fórmulas.

P26.9 incluye ahora también los dos productos de P26.8 en el total previo.
El orden sigue limitado a 10 y todos los cálculos pasan por la protección
numérica común.

## Seguridad exacta

- **Literales**: cada celda pasa por `convertir_a_numero(texto,
  limitar_entrada=True)`, que rechaza la notación científica y los números de
  más de 100 cifras antes de construir un `Fraction` (P26.2.1).
- **Intermedios**: Gauss-Jordan usa las operaciones protegidas del motor, y
  la regla 2×2 usa `multiplicar_exacto`, `restar_exacto` y `dividir_exacto`.
  Los dos productos de verificación usan esas mismas operaciones exactas
  protegidas a través del motor de producto matricial existente.
  Si los números crecen demasiado, se muestra «El cálculo produjo números
  demasiado grandes para mostrarlos de forma segura.», sin traza ni error en
  inglés.
- **Confirmación**: la firma se calcula con valores ya leídos y validados; no
  abre otro camino hacia `Fraction`.

## API

| Módulo | Pieza | Qué hace |
| --- | --- | --- |
| `backend/matriz_inversa.py` | `validar_matriz_cuadrada(a)` | `(es_valida, mensaje)`: no vacía, rectangular, exacta y cuadrada. |
| | `inversa_gauss_jordan(a)` | `[A \| I] → [I \| A⁻¹]` con los datos del procedimiento. |
| | `inversa_metodo_2x2(a)` | Regla directa; rechaza cualquier tamaño distinto de 2×2. |
| | `calcular_inversa(a, metodo)` | Elige el método (`gauss_jordan` o `directo_2x2`) y rechaza uno desconocido. |
| | `verificar_inversa(a, inversa)` | Valida dos matrices cuadradas compatibles y compara exactamente los dos productos con `I_n`, sin recalcular la inversa. |
| | `inversa_de_inversa(a, inversa, metodo)` | Invierte la inversa recibida y compara con A. |
| | `propiedad_traspuesta(a, inversa, metodo)` | Calcula y compara ambos lados mediante la traspuesta compartida. |
| | `propiedad_producto(a, inversa, b, metodo)` | Invierte B y AB, reutiliza los productos y compara ambos lados. |
| | `resolver_por_inversa(a, inversa, b)` | Calcula x = A⁻¹b y comprueba Ax = b con el motor matriz-vector. |
| | `aplicar_funcion_adicional(...)` | Contrato cerrado; devuelve función, aplicabilidad, motivo, resultado y evidencia exacta. |
| `servicios_inversa.py` | `estimar_inversa_web(entrada)` | Presupuesto compuesto del cálculo completo, incluida la regla 2×2. |
| | `confirmacion_pendiente(entrada, firma)` | `None` si se puede calcular; si no, los datos del aviso. |
| | `firmar_entrada(entrada)` | Firma de A exacta, método, verificar, función y B/b activos. |
| | `calcular_inversa_web(entrada)` | Calcula A⁻¹ una vez, verifica si se pidió, aplica la función y formatea. |
| `forms_inversa.py` | `InversaForm` | Tamaño, celdas activas A/B/b, método, función, verificar y confirmación. |
| `views.py` | `matriz_inversa` | Valida, confirma si hace falta y calcula. |

Las plantillas están en `templates/calculadora/modules/inversa/`: `index.html`,
`_confirmacion.html`, `_gauss_jordan.html`, `_metodo_2x2.html` y
`_verificacion.html`.

## Fuera de alcance

P26.9 cierra los tres teoremas y la aplicación `x = A⁻¹b` como implementados.
Siguen fuera de alcance `AX = B`,
`XA = B`, la entrada por ecuaciones, los determinantes generales, las
potencias, nuevas formas de calcular A⁻¹, las dimensiones mayores que 10 y
la generación diferida de procedimientos, un parser de expresiones y las
combinaciones arbitrarias de funciones adicionales.

## Pruebas

- `tests/test_matriz_inversa.py`: ambos métodos, ejemplos del profesor,
  consistencia (enteros, negativos, fracciones, intercambios y 400 casos
  aleatorios), validación, reutilización del motor, cota del presupuesto
  frente a los pasos reales y seguridad numérica. La verificación cubre 1×1,
  2×2 y 3×3, fracciones, negativos e intercambio de filas; ambos productos e
  identidad del orden correcto; no mutación; matrices incompatibles; y
  exactamente dos llamadas al producto existente. También comprueba que los
  métodos 2×2 coinciden en la inversa y su verificación.
- `tests/test_matriz_inversa_web.py`: catálogo, navegación y buscador, GET,
  tamaños, método predeterminado y disponibilidad del 2×2, POST válidos y
  manipulados, matrices sin inversa, separador en todas las matrices,
  procedimiento antes del resultado, Exacto / Decimal, confirmación (forzando
  la categoría y el intervalo, sin segundos reales), Cancelar, Continuar,
  firmas ajenas y recursos. P26.8 añade checkbox visible y desmarcado,
  conservación de su estado, productos dentro del procedimiento y un único
  resultado final. Los mocks comprueban una sola inversión y ningún producto
  para una matriz singular; las firmas distinguen ambos estados de
  `verificar` y conservan la validez para la misma entrada.
- Contratos transversales: teclado, desplegables, presentación numérica,
  literales peligrosos y crecimiento exacto, y estructura del procedimiento.
- `tests/test_propiedades_matriz_inversa.py`: las tres propiedades y la
  aplicación, ejemplos 2×2/3×3, fracciones, negativos, ambos métodos, no
  mutación, dimensiones, singularidad y mocks de los motores compartidos.
- `tests/test_propiedades_inversa_form.py` y
  `tests/test_propiedades_inversa_web.py`: contrato cerrado y celdas
  condicionales, flujo sin JS con Aplicar, método únicamente en 2×2,
  resultados únicos, verificación independiente, presupuesto compuesto y
  firma completa. El ejemplo del profesor devuelve x = `[5, -3]` también por POST.
- `python -m tests.inversa_browser`, en
  `http://127.0.0.1:8879/__pruebas/`: regresiones con DOM real sobre la
  aplicación, tamaño 2→3→2, B/b condicionales, supervivencia de celdas,
  teclado y salida/confirmación obsoletas. No añade dependencias.
