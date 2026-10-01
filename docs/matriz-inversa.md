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
búsquedas siguen llevando solo a Reducción por filas. Ni el catálogo ni los
controles muestran fórmulas.

## Entrada

`InversaForm` (`forms_inversa.py`) hereda de `FormularioCeldas`, igual que
Operaciones con matrices y Resolver Ax = b. Reutiliza las celdas
`celda_A_i_j`, el parser común y el contrato HTTP estricto: se rechazan celdas
de más o de menos, campos ajenos o repetidos. Como A es cuadrada, la estructura
es un solo control, **Filas y columnas**, de 1 a 10 (`DIMENSION_MAXIMA`; no se
amplía en este incremento). `inversa.js` regenera la cuadrícula con las mismas
plantillas inertes que el servidor y conserva lo escrito. Sin JavaScript,
**Aplicar** redibuja la estructura.

El método se elige con dos radios: **Gauss-Jordan**, el predeterminado, y
**Método para matrices 2×2**. El segundo solo está disponible si A es 2×2:

- el servidor lo dibuja desactivado con cualquier otro tamaño
  (`RadioConInactivas`), y un control desactivado no viaja en el POST;
- `inversa.js` lo desactiva al cambiar el tamaño y, si estaba elegido, vuelve a
  marcar Gauss-Jordan;
- un POST manipulado con `metodo=directo_2x2` y otro tamaño se rechaza con
  «El método para matrices 2×2 solo se puede usar cuando A es 2×2.», y el
  backend lo rechaza también.

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
3. **Matriz final**: si se llegó a `[I | B]`, el bloque derecho B es la
   inversa; si no, qué filas del lado izquierdo quedaron con solo ceros.

La página no habla de sistemas, de b, de ecuaciones ni de clasificación.

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

## Resultado y Exacto / Decimal

`servicios_inversa.calcular_inversa_web` no calcula: llama a
`calcular_inversa(a, metodo)` y formatea los datos exactos. El resultado va al
final, una sola vez: `A⁻¹ =` con la matriz, o el mensaje de matriz no
invertible. La palabra «Resultado» no aparece dentro del procedimiento. La
cadena del método 2×2 termina en la matriz obtenida, como las cadenas de
Operaciones con matrices; la matriz final de Gauss-Jordan es `[I | A⁻¹]`.

`#resultado` va envuelto en `{% numeric_results %}` y la página carga
`numeros.js`. Por ejemplo, la inversa de la matriz 3×3 del profesor muestra
`-9/2`, `3/2` y `1/2` como `-4.5`, `1.5` y `0.5` sin recalcular. El backend
nunca pasa a `float`.

## Ejemplos del profesor

| A | Método | Resultado |
| --- | --- | --- |
| `[[3, 4], [5, 6]]` | Gauss-Jordan y 2×2 | `A⁻¹ = [[-3, 2], [5/2, -3/2]]` |
| `[[0, 1, 2], [1, 0, 3], [4, -3, 8]]` | Gauss-Jordan (empieza con `F1 <-> F2`) | `A⁻¹ = [[-9/2, 7, -3/2], [-2, 4, -1], [3/2, -2, 1/2]]` |
| `[[1, 2], [2, 4]]` | ambos | La matriz no tiene inversa. |
| `[[4]]` | Gauss-Jordan (el 2×2 queda desactivado) | `A⁻¹ = [[1/4]]` |

## Presupuesto y confirmación

Es la primera integración visible de P26.2. Antes de ejecutar Gauss-Jordan,
`estimar_inversa_web` calcula

```python
estimar_gauss_jordan(n, 2 * n, columnas_pivote=n, perfil=perfil_numerico(a))
```

sin ejecutar nada, y `categoria` decide:

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

Como el aviso vive dentro del formulario, la matriz y el método se conservan:

- **Cancelar** envía `ajustar`, igual que Aplicar: redibuja sin calcular.
- **Continuar** envía `confirmacion` con una firma HMAC (`salted_hmac` con
  SHA-256 y la clave de Django) del método y los valores exactos de A.
  `confirmacion_pendiente` recalcula esa firma y la compara con
  `constant_time_compare`. Con la firma correcta se calcula sin volver a
  preguntar, así que no hay bucle. Con otra matriz, otro método o una firma
  inventada, se vuelve a estimar y a preguntar. La misma matriz escrita de otra
  forma (`2/2` en lugar de `1`) es la misma entrada.
- Es el servidor quien exige la confirmación; JavaScript solo oculta un aviso
  que dejó de corresponder cuando el usuario edita la matriz.

La regla 2×2 hace unas pocas operaciones y nunca pide confirmación.

Con las referencias actuales, una 9×9 de enteros queda como perceptible y una
10×10 como pesada (referencia de 3,6 s; intervalo de 1,2 a 10,9 s). En el
equipo de desarrollo, el POST completo midió 1,7 s para 9×9 y 2,7 s para
10×10, dentro del intervalo; desde 6×6 la referencia queda entre un 25 y un
35 % por encima de lo medido. Este incremento no cambia referencias, umbrales
ni fórmulas.

## Seguridad exacta

- **Literales**: cada celda pasa por `convertir_a_numero(texto,
  limitar_entrada=True)`, que rechaza la notación científica y los números de
  más de 100 cifras antes de construir un `Fraction` (P26.2.1).
- **Intermedios**: Gauss-Jordan usa las operaciones protegidas del motor, y
  la regla 2×2 usa `multiplicar_exacto`, `restar_exacto` y `dividir_exacto`.
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
| `servicios_inversa.py` | `estimar_inversa_web(entrada)` | Estimación de Gauss-Jordan sobre `[A \| I]`; `None` con la regla 2×2. |
| | `confirmacion_pendiente(entrada, firma)` | `None` si se puede calcular; si no, los datos del aviso. |
| | `firmar_entrada(entrada)` | Firma de la matriz exacta y el método. |
| | `calcular_inversa_web(entrada)` | Datos listos para la plantilla. |
| `forms_inversa.py` | `InversaForm` | Tamaño, celdas, método y confirmación. |
| `views.py` | `matriz_inversa` | Valida, confirma si hace falta y calcula. |

Las plantillas están en `templates/calculadora/modules/inversa/`: `index.html`,
`_confirmacion.html`, `_gauss_jordan.html` y `_metodo_2x2.html`.

## Fuera de alcance

Llegan en incrementos posteriores: resolver sistemas mediante la inversa, la
entrada por ecuaciones, la verificación `A⁻¹A = AA⁻¹ = I` seleccionable, los
teoremas de la inversa de la inversa, de AB y de la traspuesta, los
determinantes generales, las dimensiones
mayores que 10 y la generación diferida de procedimientos.

## Pruebas

- `tests/test_matriz_inversa.py`: ambos métodos, ejemplos del profesor,
  consistencia (enteros, negativos, fracciones, intercambios y 400 casos
  aleatorios), validación, reutilización del motor, cota del presupuesto
  frente a los pasos reales y seguridad numérica.
- `tests/test_matriz_inversa_web.py`: catálogo, navegación y buscador, GET,
  tamaños, método predeterminado y disponibilidad del 2×2, POST válidos y
  manipulados, matrices sin inversa, separador en todas las matrices,
  procedimiento antes del resultado, Exacto / Decimal, confirmación (forzando
  la categoría y el intervalo, sin segundos reales), Cancelar, Continuar,
  firmas ajenas y recursos.
- Contratos transversales: teclado, desplegables, presentación numérica,
  literales peligrosos y crecimiento exacto, y estructura del procedimiento.
