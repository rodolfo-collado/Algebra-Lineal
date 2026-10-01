# Presupuesto computacional

[Índice de documentación](README.md) · [Portada](../README.md)

`backend/presupuesto_computacional.py` estima cuánto trabajo pide una operación
**válida** antes de ejecutarla. No rechaza nada: separa lo que la interfaz no
puede recibir (un límite) de lo que simplemente tarda (un costo). El módulo no
depende de Django ni de la interfaz. La historia, la auditoría y las mediciones
del presupuesto de entrada de Reducción por filas siguen en
[Presupuesto de entrada de Sistemas](presupuesto-sistemas.md).

## Límite estructural y costo estimado

| | Límite estructural | Costo estimado |
| --- | --- | --- |
| Pregunta | ¿Se puede recibir y representar esta entrada sin riesgo? | ¿Cuánto trabajo pide una entrada ya aceptada? |
| Si se supera | Se rechaza con un mensaje, antes de reservar estructuras. | Nada, por ahora. Más adelante, un aviso con opción de continuar. |
| Dónde vive | `presupuesto_sistemas.py`, `operandos.py` y los formularios. | `presupuesto_computacional.py`. |

Un costo alto no convierte una entrada en inválida. Un sistema 10×10 con
fracciones es un ejercicio correcto aunque su procedimiento tarde varios
segundos en mostrarse: no hay error matemático ni de entrada que señalar. Por
eso estimar nunca lanza un error por costo; solo rechaza datos que no describen
ninguna operación, como una dimensión que no es un entero positivo.

### Límites actuales

P26.2 no cambia ningún límite. Clasificados por lo que protegen:

| Límite | Valor | Qué protege |
| --- | ---: | --- |
| Campos por envío (`DATA_UPLOAD_MAX_NUMBER_FIELDS` de Django) | 1000 | Seguridad: Django responde 400 antes de la vista. |
| Texto de un sistema | 10000 caracteres | Seguridad: el análisis queda acotado antes de dividir el texto. |
| Cifras por componente y notación científica, en Sistemas | 100; rechazada | Seguridad: `Fraction` no llega a construir enteros gigantes. |
| Valor agrupado, en Sistemas | lo que da un literal | Seguridad y representación: sumar términos no crea valores que una celda no admite. |
| Ecuaciones, variables y celdas de Sistemas | 12, 12 y 120 | Estructura y, sobre todo, volumen del procedimiento: cada paso guarda dos matrices. |
| Operandos y celdas de Matrices y Vectores | 50 y 900 | Estructura: un campo HTML por celda cabe en los 1000 campos de Django. |
| Dimensión de matrices y vectores | 10 | Estructura y representación: cuadrículas editables legibles. |

Ninguno mide el tiempo del cálculo matemático: el motor de un sistema 12×12
tarda milisegundos. El tope de Sistemas se eligió midiendo el POST completo,
donde domina el procedimiento (ver [Costo observado](presupuesto-sistemas.md#costo-observado)),
y los topes de literales evitan trabajo desproporcionado al leer un número.

## Qué estima

Una `Estimacion` describe el peor caso denso de una operación a partir de sus
dimensiones, sin ejecutarla ni recorrer la matriz:

- `pasos`: pasos que registra el procedimiento (operaciones de fila o entradas del producto);
- `calculo`: operaciones aritméticas con números exactos;
- `procedimiento`: valores que los pasos conservan y que luego se presentan;
- `factor_numerico`: cuánto encarece cada operación el tamaño de los números (1 con números pequeños);
- `partes`: las estimaciones que forman una compuesta.

`calculo` y `procedimiento` ya incluyen el efecto del tamaño de los números. Son
cantidades, no tiempos: no dependen del equipo y las pruebas las comprueban de
forma exacta. Con r = mín(m, columnas con pivote) y e = pasos − r, las
eliminaciones:

| Operación | Pasos (cota) | Cálculo | Procedimiento |
| --- | --- | --- | --- |
| Gauss, m×c | r·m − r(r − 1)/2 | c·(r + 2e) | 2·m·c por paso |
| Gauss-Jordan, m×c | r·m | c·(r + 2e) | 2·m·c por paso |
| Producto, m×n · n×p | m·p | 2·m·n·p | m·p·(3n + 1) + p·(m·n + m + n) + m·n |

Normalizar divide toda la fila y eliminar multiplica y resta en cada columna.
Un intercambio de filas sí registra un paso, pero no aumenta la cota. Solo hace
falta si la fila que estaba en la posición del pivote tenía 0 en esa columna; al
bajar tras el intercambio, esa fila no necesita una eliminación en esa columna.
Así, el intercambio sustituye dentro de la cota a una eliminación que el peor
caso denso ya había contado. La cota vale también con intercambios y se alcanza
en el peor caso; las pruebas la comparan con los pasos reales de los motores en
matrices cuadradas, rectangulares, con ceros y con intercambios. En el producto,
el procedimiento son las evidencias de sus dos lecturas (fila por columna y por
columnas).

## Cálculo y procedimiento

En Gauss-Jordan de n×(n + 1), el cálculo crece como n³ y el procedimiento como
n⁴. El motor de un sistema 12×13 termina en unos milisegundos, pero su
procedimiento guarda hasta 44 928 valores; pasarlos a texto ya cuesta veinte
veces más que el motor, y mostrarlos en la página, mucho más. En un perfil del
POST 10×10 con «Comparar ambos», unas tres cuartas partes del tiempo se fueron
en `{% numeric_results %}`, que prepara las variantes Exacto/Decimal de cada
número en los 9 MiB de HTML.

Que un motor termine rápido no significa que mostrar su procedimiento sea
barato. Por eso la estimación mantiene separadas ambas partes: una interfaz
podrá, por ejemplo, contar solo el cálculo cuando el procedimiento no se muestre.

## Tamaño de los números

PyGebra calcula con `Fraction`, y dos matrices 10×10 cuestan muy distinto si
una tiene enteros pequeños y la otra fracciones largas. `perfil_numerico(*matrices)`
mide los bits del mayor numerador y del mayor denominador con `bit_length()`,
que no depende del tamaño del número: no convierte nada a texto ni vuelve a
leer literales. Las protecciones de literales siguen actuando antes, al
convertir el texto; el perfil solo recibe valores ya leídos.

Los racionales crecen con cada eliminación, y al combinar filas se acumulan los
denominadores de todas sus columnas. Por eso cada operación define sus bits
efectivos:

| Operación | Bits efectivos |
| --- | --- |
| Gauss y Gauss-Jordan | r × (bits del numerador + (c − 1) × bits del denominador) |
| Producto | 2 × bits del numerador + n × bits del denominador |

Con ellos, el cálculo se multiplica por `1 + (bits / 1000) ** 1.25`, porque la
aritmética con enteros grandes crece más que lineal, y el procedimiento por
`1 + bits / 7000`, porque mostrar un número crece con la longitud de su texto.

Con fracciones de 20 cifras, Gauss-Jordan 12×13 fue 19 veces más lento que con
enteros pequeños, y 2,7 veces en 4×5; el factor predice 19,5 y 2,4. En 48 casos
de Gauss-Jordan y producto, con enteros de hasta 100 cifras y fracciones de
hasta 20, el factor quedó entre 0,6 y 1,4 veces lo medido. En el POST completo,
fracciones de 10, 20 y 50 cifras encarecieron la página solo entre 1,2 y 1,5
veces, como predice el factor lineal. No es una predicción exacta: no sabe de
cancelaciones ni de valores concretos.

## Operaciones compuestas

`combinar_estimaciones(*partes, operacion=...)` suma pasos, cálculo y
procedimiento, conserva las partes y toma el mayor factor numérico. No hace
falta un estimador por pantalla. Resolver un sistema con la matriz inversa se
expresa con las piezas existentes:

```python
perfil = perfil_numerico(a, [b])
estimacion = combinar_estimaciones(
    estimar_gauss_jordan(n, 2 * n, columnas_pivote=n, perfil=perfil),  # [A | I] → [I | A⁻¹]
    estimar_producto(n, n, 1, perfil=perfil),                          # A⁻¹b
    estimar_producto(n, n, n, perfil=perfil),                          # verificación A⁻¹A
    operacion="sistema_por_inversa",
)
```

Para un operando que todavía no existe, como A⁻¹, se usa el perfil de la
entrada. Sus valores suelen ser más grandes, así que esa parte queda optimista.

## Tiempo: referencias calibrables

El tiempo depende del equipo, así que se deriva aparte, con constantes que el
código nombra como referencias:

| Referencia | Valor | Origen |
| --- | ---: | --- |
| `REFERENCIA_SEGUNDOS_OPERACION` | 1 µs | Motores con enteros pequeños en el benchmark. |
| `REFERENCIA_SEGUNDOS_CELDA` | 90 µs | POST completo de «Comparar ambos» (`--web`), de 6×7 a 10×11. |
| `REFERENCIA_MARGEN` | 3 | El intervalo va de la referencia / 3 a la referencia × 3. |
| `REFERENCIA_UMBRALES` | 1, 3 y 10 s | Normal, perceptible, pesada y muy pesada. |
| `REFERENCIA_BITS`, `REFERENCIA_EXPONENTE`, `REFERENCIA_BITS_TEXTO` | 1000, 1,25 y 7000 | Tamaño de los números. |

- `segundos_referencia(estimacion)`: cálculo × 1 µs + procedimiento × 90 µs.
- `intervalo_segundos(estimacion)`: la referencia / 3 y la referencia × 3.
- `categoria(estimacion)`: `Categoria.NORMAL` (menos de 1 s), `PERCEPTIBLE`
  (menos de 3 s), `PESADA` (menos de 10 s) o `MUY_PESADA`.

Las categorías son valores, no textos. La interfaz decide qué decir, por
ejemplo «Esta operación puede tardar varios segundos. ¿Quieres continuar?», y no
muestra operaciones elementales, complejidad, bits ni memoria. Desde P26.4,
Matriz inversa muestra ese aviso (ver [Integración actual](#integración-actual)).

Las mediciones históricas de [Costo observado](presupuesto-sistemas.md#costo-observado)
caen dentro del intervalo de referencia (10×10: 2,46 s medidos, intervalo de
1,0 a 9,3 s) y su orden por tamaño coincide con el del modelo; una prueba lo
comprueba sin mirar segundos.

## Limitaciones

- Las cantidades son cotas del peor caso denso: con ceros, pivotes iguales a 1 o
  variables libres hay menos pasos. La cota nunca queda por debajo de los pasos reales.
- El perfil usa el mayor valor de la entrada. No prevé cancelaciones ni el
  tamaño de operandos que aún no existen.
- Las referencias salen de un solo equipo y cambian con su carga. El mismo POST
  10×10 con «Comparar ambos» tardó 2,46 s en la medición histórica, 3,0 s en
  este incremento y hasta 11,5 s con otras aplicaciones ocupando cerca del 40 %
  de la CPU. Por eso el tiempo se expresa como intervalo y categoría, nunca como
  una cifra, y conviene recalibrar con `--web` en un equipo representativo antes
  de usar las categorías para pedir confirmaciones.
- Una página tiene además un costo fijo, de unas centésimas de segundo, que el
  modelo no cuenta. No cambia la categoría de nada.
- Hallazgo fuera del alcance original de P26.2: Python no convierte a texto enteros de más
  de 4300 cifras. Con fracciones de 100 cifras, dentro del presupuesto de
  literales de Sistemas, un sistema 6×6 alcanza ese límite durante la
  eliminación y el error se muestra en inglés. Es un límite de representación,
  no un costo, y la estimación no lo corrige. P26.2.1 lo resuelve por separado en
  [Protección numérica común](seguridad-numerica.md), sin cambiar categorías,
  referencias, dimensiones ni fórmulas de costo.

## Integración actual

Los servicios pueden consultar la estimación antes de ejecutar:

- `servicios.estimar_entrada_web(tipo_entrada, metodo, *, texto=None, matriz_aumentada=None)`
  estima Reducción por filas. Lee la entrada con `_leer_entrada`, la misma
  función que usa `resolver_entrada_web`, así que el texto pasa por el parser con
  presupuesto y la matriz por `validar_dimensiones` antes de contar nada. Los
  pivotes se buscan solo en las columnas de coeficientes, como en los motores, y
  «Comparar ambos» suma los dos métodos.
- `servicios_ecuaciones.estimar_ecuacion_web(entrada)` estima Ax = b: por cada
  método, la reducción de [A | b] más el producto A·x de la comprobación, que se
  cuenta siempre porque antes de resolver no se sabe si la solución es única.

Las vistas de esas dos herramientas todavía no las llaman: no hay aviso,
confirmación ni cambio en su flujo, y ninguna entrada válida se rechaza por su
costo. Una prueba lo fija forzando que todo sea muy pesado y comprobando que
ambas páginas siguen resolviendo.

Matriz inversa (P26.4) es la primera integración visible.
`servicios_inversa.estimar_inversa_web(entrada)` estima Gauss-Jordan sobre
`[A | I]` con `estimar_gauss_jordan(n, 2 * n, columnas_pivote=n, perfil=perfil_numerico(a))`
antes de ejecutar. Con `Categoria.PESADA` o `MUY_PESADA`, la vista no calcula:
muestra un aviso con el intervalo de `intervalo_segundos` y espera a que el
usuario pulse **Continuar**. El servidor exige una firma de esa misma entrada, así
que la confirmación no sirve para otra matriz ni depende de JavaScript. La regla
2×2 no se estima. Tampoco aquí se rechaza nada por su costo: la entrada sigue
siendo válida y el usuario decide. Consulta
[Matriz inversa](matriz-inversa.md#presupuesto-y-confirmación).

## Benchmark

`scripts/benchmark_presupuesto.py` mide Gauss, Gauss-Jordan y el producto de
matrices con entradas deterministas: `random.Random(42)`, enteros entre −5 y 5
con 30 en la diagonal (como las mediciones históricas) y una segunda serie de
fracciones cuyo numerador y denominador tienen la cantidad de cifras indicada.
No forma parte de `unittest discover` ni de CI; las pruebas solo comprueban que
sus entradas se repiten.

```bash
uv run python -m scripts.benchmark_presupuesto
uv run python -m scripts.benchmark_presupuesto --tamanos 14 16 20 --digitos 30
uv run python -m scripts.benchmark_presupuesto --web
```

| Opción | Efecto |
| --- | --- |
| `--tamanos` | n de los sistemas n×(n + 1) y de los productos n×n · n×n. Por defecto 2, 4, 6, 8, 10 y 12. |
| `--digitos` | Cifras del numerador y del denominador en la segunda serie. Por defecto 10. |
| `--repeticiones` | Ejecuciones por caso; se informa la mediana. Por defecto 3. |
| `--web` | Mide además el POST completo de «Comparar ambos» en Reducción por filas; omite los tamaños fuera del presupuesto de entrada. |

Cada fila muestra la operación, las dimensiones, los valores, la mediana, los
pasos reales, la cota estimada y el factor numérico. «µs/unidad» divide la
mediana entre el cálculo estimado y «µs/celda», entre el procedimiento
estimado: si el modelo es bueno, se parecen entre tamaños y entre enteros y
fracciones, y su valor orienta las referencias. Un caso que Python no puede
pasar a texto aparece como «no terminó», igual que fallaría en la aplicación.

### Resultados locales

Windows 11, Python 3.13.3, 29 de septiembre de 2026, en el equipo de desarrollo
con otras aplicaciones abiertas (entre el 30 y el 45 % de la CPU ocupada).
Extracto de `uv run python -m scripts.benchmark_presupuesto --web`:

| Motor | Dimensiones | Valores | Mediana | Pasos / cota | Factor | µs/unidad |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Gauss | 12×13 | enteros | 2,0 ms | 77 / 78 | 1,04 | 1,04 |
| Gauss-Jordan | 12×13 | enteros | 3,7 ms | 143 / 144 | 1,04 | 0,99 |
| Gauss-Jordan | 12×13 | 10 cifras | 24,0 ms | 144 / 144 | 8,78 | 0,76 |
| Producto AB | 12×12 · 12×12 | enteros | 4,5 ms | 144 entradas | 1,00 | 1,29 |
| Producto AB | 12×12 · 12×12 | 10 cifras | 8,6 ms | 144 entradas | 1,38 | 1,79 |

Desde 6×7, «µs/unidad» se mantiene entre 0,8 y 1,4 en Gauss y Gauss-Jordan,
con enteros y con fracciones, aunque el factor numérico llega a 8,8: el modelo
del cálculo sigue al motor. En el producto con fracciones queda algo por encima
(de 1,6 a 2,5). Pasar a texto los pasos de Gauss-Jordan 12×13 tardó 81 ms,
veinte veces lo que tardó el motor.

POST completo de «Comparar ambos», en dos ejecuciones del mismo día:

| Dimensiones | Valores | Equipo tranquilo | Equipo cargado | Referencia | Intervalo |
| --- | --- | ---: | ---: | ---: | ---: |
| 6×7 | enteros | 0,46 s | 1,17 s | 0,43 s | 0,14 – 1,30 s |
| 8×9 | enteros | 1,35 s | 3,79 s | 1,31 s | 0,44 – 3,92 s |
| 10×11 | enteros | 3,02 s | 6,84 s | 3,10 s | 1,03 – 9,30 s |
| 10×11 | 10 cifras | 4,63 s | 8,77 s | 4,68 s | 1,56 – 14,05 s |

Con el equipo tranquilo, la referencia quedó a menos de un 12 % de lo medido
desde 6×7, también con fracciones de 20 y 50 cifras. Con el equipo cargado todo
tardó entre dos y tres veces más, todavía dentro del intervalo; en otro momento
de carga, el mismo 10×11 con enteros llegó a 11,5 s, fuera de él. La forma del
modelo se mantiene (µs/celda casi igual con enteros y con fracciones); la
escala depende del equipo.

## Añadir una operación al presupuesto

1. Cuenta, no ejecutes: escribe `estimar_<operación>(dimensiones…, *, perfil=None)`
   en `backend/presupuesto_computacional.py`. A partir de las dimensiones,
   calcula los pasos que registraría el motor, sus operaciones aritméticas y los
   valores que guardaría su procedimiento en el peor caso denso, siguiendo lo
   que el motor realmente guarda en cada paso.
2. Decide cómo crecen los números en esa operación (se acumulan entre pasos,
   como en una eliminación, o no, como en un producto), exprésalo como bits
   efectivos del `PerfilNumerico` y aplica `_factor_numerico` al cálculo y
   `_factor_texto` al procedimiento.
3. Si la operación es una secuencia de otras que ya tienen estimador (una
   inversa y su verificación, una cadena de productos), no escribas uno nuevo:
   usa `combinar_estimaciones`.
4. Prueba que la cota acota los pasos reales del motor en matrices cuadradas,
   rectangulares y con ceros, que el costo crece con cada dimensión y que
   estimar no ejecuta el motor. No pruebes segundos.
5. Mide: añade la operación al benchmark y comprueba que su «µs/unidad» se
   parece al de las demás. Si no, revisa la cuenta antes de tocar las referencias.
6. En la interfaz, usa `categoria` o `intervalo_segundos`, nunca los números internos.

El benchmark histórico conserva su ruta POST `/sistemas/` y sus mediciones;
P26.5 procesa ese POST con la misma vista y devuelve 200, sin redirección ni
cambio de presupuesto. Los formularios y enlaces nuevos usan la ruta canónica.

## Estado de incrementos

- P26.3, Gauss-Jordan con aumentos de varias columnas: `estimar_gauss_jordan(n, 2 * n, columnas_pivote=n)`
  ya describe [A | I]. Si el motor cambia lo que guarda cada paso, se actualiza
  la cuenta de valores del procedimiento.
- P26.4, Matriz inversa: ya estima antes de ejecutar y decide con `categoria`.
  El POST completo midió 1,7 s en 9×9 y 2,7 s en 10×10 con enteros, dentro del
  intervalo; la referencia queda entre un 25 y un 35 % por encima. Las
  referencias no se recalibraron; conviene hacerlo con `--web` y la herramienta
  real en un equipo representativo.
- P26.5, Reducción por filas: reorganiza la herramienta bajo Matrices; no
  cambia el presupuesto, los motores ni los identificadores de método.
- P26.6, consolidación de Operaciones/Expresiones: queda fuera de P26.5.
- Sistema por inversa: la composición de arriba sigue siendo una aplicación
  futura; P26.5 no la implementa.
- P26.8, verificaciones de inversa: una `estimar_producto(n, n, n)` por cada una, sumada a
  la estimación.
