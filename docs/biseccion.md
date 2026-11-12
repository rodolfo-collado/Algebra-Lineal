# Bisección y gráfica interactiva

[Índice](README.md) · [Arquitectura](arquitectura.md) · [Pruebas](pruebas.md)

Disponible en **Métodos numéricos → Raíces de ecuaciones → Método de bisección**,
en `/metodos-numericos/biseccion/`, tanto en Django como en Windows sin Internet.
Comparte la exploración, el teclado y la presentación con [Regla falsa](regla-falsa.md);
cada método conserva su algoritmo y su criterio de parada.

## Uso

Escribe `f(x)` para explorar su gráfica en una ventana inicial `[-10, 10]`, sin
completar `a` ni `b`. Para calcular, elige el extremo inferior `a` y el superior
`b` y pulsa **Resolver por bisección**. Función y extremos empiezan vacíos; los ajustes conservan sus valores
predeterminados. Al enfocar la función aparece el teclado contextual de PyGebra:
x, x², x³, exponente general, paréntesis, operaciones, seno, coseno, raíz, ln, log₁₀ y las constantes π y e.
Las teclas x² y x³ conservan esos superíndices en el campo, igual que Aᵀ conserva
la traspuesta en matrices. La tecla aⁿ activa o desactiva el modo superíndice,
con estado visual seleccionado y `aria-pressed`. La ayuda existente anuncia el
modo activo. Escribe x, activa aⁿ, escribe 12 (con teclado físico o las teclas de
dígitos), desactívalo y continúa con +3: queda x¹²+3. No se abre ningún diálogo.
Un signo al inicio del exponente permite x⁻³; tras sus dígitos, un signo se trata
como operación normal y desactiva el modo. Otras operaciones también lo desactivan.
Mover el cursor o seleccionar texto permite editar un exponente; borrar y Deshacer
usan la edición nativa. Al salir del campo o pulsar Escape se desactiva el modo.
Pegar texto o usar composición conserva la entrada original y sale del modo.
Para exponentes fraccionarios o expresiones utiliza ^ o ** con paréntesis.
La tecla √ inserta √() con el cursor dentro; sqrt() sigue siendo compatible.
La tecla sen inserta sen(); sin() es un alias del mismo seno en radianes.
Los alias producen el mismo árbol, resultado, gráfica y clave de comparación.
Escribe sen(x)² para elevar el resultado del seno; sen²(x) no se admite.
También puedes
escribir con el teclado físico. La gráfica se actualiza al editar la función;
desplazarla o cambiar el zoom solicita nuevas muestras al servidor local, sin
resolver de nuevo. La rueda del ratón sobre la gráfica acerca o aleja y arrastrar
la desplaza. **Elegir a/b** permite pulsar sobre la curva para llevar
la coordenada x muestreada al formulario; luego puedes ajustar el valor arrastrando
su línea discontinua o escribiendo con teclado. Editar extremos no mueve los ejes
ni exige que el intervalo ya sea válido. Resolver sí comprueba todas las condiciones.
**Vista inicial** vuelve a `[-10, 10]`; después de resolver se encuadra la primera
iteración y **Enfocar intervalo** encuadra la iteración activa. La franja y los marcadores
de las iteraciones conservan la evidencia del cálculo anterior cuando editas la entrada.

**Ajustes y funciones admitidas** permite reducir la precisión predeterminada
`0.0001`, y cambiar el límite de 200 iteraciones (entre 1 y 1000). La precisión
debe ser positiva y nunca mayor que `0.0001`, también en envíos HTTP manipulados.

Se admiten `+`, `-`, `*`, `/`, `^` o `**`, paréntesis, la variable `x`, constantes
`pi` y `e`, y funciones de un argumento: `sen` (alias `sin`), `cos`, `tan`, `exp`, `log`/`ln`
(logaritmo natural), `log10`, `√()` (alias `sqrt()`) y `abs`. Los ángulos se expresan en radianes.
La multiplicación puede ser explícita o implícita: `5*x^3` y `5x^3`, `2*(x+1)`
y `2(x+1)`, `x*(x+1)` y `x(x+1)`, o `(x+1)*(x-1)` y `(x+1)(x-1)`.
También se admiten `2sen(x)`, `sen(x)cos(x)` y `pi x`. Se insertan productos
entre factores reconocidos antes de validar el AST; no se separan nombres:
`xx`, `xpi` y `senx` son inválidos. `sen(x)` y `log(x)` siguen siendo llamadas.
Los números científicos completos (`1e-3`, `2E+2`) se conservan; `2e` se rechaza
por ambiguo: escribe `2*e` para la constante. Productos y divisiones tienen igual
prioridad y se agrupan de izquierda a derecha: `1/2x` es `(1/2)*x`; para dividir
por todo el producto escribe `1/(2x)`. Los exponentes no pueden depender de `x`.
Ambas notaciones generan la misma clave de comparación y los mismos resultados.

Para preparar una demostración oral, consulta la [guía de exposición](guia-exposicion-biseccion.md).

El resultado y su estado aparecen antes de la gráfica. La zona de estudio, la
reproducción y la tabla se describen en [la interfaz compartida](newton-raphson.md#zona-de-estudio-compartida).
La franja clara resalta el intervalo **antes** del recorte, la intensa la mitad que se
conserva, una línea punteada baja del punto medio del eje a f(c) y los tres
marcadores muestran `(a,f(a))`, `(c,f(c))` y `(b,f(b))`. Estas interacciones usan
el JSON calculado, sin peticiones ni una nueva ejecución del algoritmo. La lectura
identifica a (izquierdo), c (punto medio) y b (derecho), muestra los signos reales
y explica qué mitad se descarta, que c sustituye al extremo con su mismo signo,
cuál permanece y el nuevo intervalo. Distingue el intervalo antes de dividirlo del
resultante; un cero calculado tiene su propia explicación. El resumen usa cifras
legibles, aumentando las cifras si hace falta distinguir los extremos. La lectura
completa de la iteración activa está en **Procedimiento detallado**.

**Verificación** separa condición, valores y conclusión para tres preguntas: por qué
hay una raíz (continuidad y signos iniciales, o raíz en extremo), si se alcanzó la
precisión (resta b − a final y comparación con la tolerancia), y por qué f(c) puede
no ser cero. Distingue raíz calculada, parada por longitud, máximo de iteraciones
y estancamiento, sin afirmar unicidad ni usar el error relativo como parada.
Un cero en aritmética de máquina no prueba un error matemático exactamente cero.

Para probar otro intervalo, cambia `a` y `b` y vuelve a resolver: la función se
conserva. Desde la segunda ejecución aparece el **Historial de esta sesión**, con los
intervalos de cada función agrupados y comparables. Dos aproximaciones parecidas no
demuestran que sea la misma raíz ni que sea única. Una edición marca el resultado
como anterior.

## Algoritmo y comprobaciones

La referencia principal es `MÉTODOS NUMERICOS (1).pptx`, diapositivas 3 y 6,
facilitada para esta tarea. La guía `guia-busqueda-raices.pdf` es complementaria.
Se mantiene el orden de las diapositivas:

1. Validar extremos finitos, `a < b`, precisión y límite de iteraciones.
2. Comprobar dominio/continuidad mediante una envolvente conservadora de la
   expresión, evaluar los extremos y atender una raíz en cualquiera de ellos.
3. Exigir signos opuestos sin multiplicar valores que podrían desbordarse.
4. Calcular manualmente `c = a + (b-a)/2`, equivalente al punto medio y más
   resistente al desbordamiento de `a+b`; evaluar `f(c)`.
5. Si `f(c)=0`, terminar. En otro caso, conservar `[a,c]` o `[c,b]` según su signo.
6. Parar cuando la longitud **después del recorte** sea estrictamente menor que
   la precisión. Si se agota el límite o el punto medio ya no es representable
   entre los extremos, informar **sin convergencia**.
7. Volver a evaluar `f(c)` independientemente antes de devolver el resultado.

La longitud restante y el error relativo porcentual son medidas diferentes.
El segundo es `abs((c_n-c_anterior)/c_n)*100`; no está definido en la primera
iteración, si `c_n=0`, o si su valor excede el rango numérico. Nunca decide la
parada. El residuo `f(c)` también se presenta por separado: no tiene las unidades
de `x` y no debe compararse automáticamente con la tolerancia del intervalo.
El último `c` es un extremo del intervalo final; su cota de distancia a una raíz
es la longitud restante, no su mitad, bajo las comprobaciones de continuidad y
la precisión de máquina.

## Ejemplos verificados

Para `x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10`, con precisión `0.0001`:

| Intervalo | Iteraciones | Último c | f(c), aproximadamente | Longitud restante |
|---|---:|---:|---:|---:|
| [0.55, 1.1] | 13 | 0.763970947265625 | -0.000669776157658 | 0.000067138671875 |
| [5, 5.5] | 13 | 5.23602294921875 | -0.00707856997315 | 0.00006103515625 |
| [5.2, 5.3] | 10 | 5.23603515625 | -0.00515962563064 | 0.00009765625 |

Los dos últimos intervalos finales se solapan y aproximan la raíz cercana a
`5.23607`; sus residuos no necesitan ser menores que `0.0001` para cumplir la
cota de longitud en `x`.

La secuencia de puntos medios del ejemplo de trece iteraciones es:
`0.825, 0.6875, 0.75625, 0.790625, 0.7734375, 0.76484375, 0.760546875,
0.7626953125, 0.76376953125, 0.764306640625, 0.7640380859375,
0.76390380859375, 0.763970947265625`.

La diapositiva 6 muestra errores como fracciones aunque la fórmula de la 3
incluye el factor 100. Aquí la segunda iteración muestra **20 %**, no `0.2 %`.
Su última fila repite valores anteriores de la función; se recalculan todos.
La página 1 del PDF usa otro criterio (error relativo menor al 1 %) y da
evaluaciones incompatibles con el polinomio: por ejemplo, `f(0.55)` es
`3.36088125`, no `3.1098`. No se copian sus aproximaciones.

## Seguridad y límites

`backend/funciones_reales.py` interpreta un AST con una lista cerrada de nodos y
funciones; no usa `eval`, `exec`, importaciones dinámicas ni generación de código.
Limita longitud, nodos y profundidad, y detecta desbordamientos, subdesbordamientos
a cero y resultados no finitos. La bisección está en `backend/biseccion.py` y no
utiliza un solver externo. No se añadieron dependencias Python.

La envolvente de intervalos comprueba que las operaciones admitidas conservan
dominio real y continuidad. Es conservadora: puede rechazar expresiones válidas
si sus cotas incluyen un denominador cero o un argumento fuera del dominio;
conviene reducir el intervalo o reescribir la expresión. No es álgebra simbólica
ni aritmética exacta. El cero calculado se identifica como cero en aritmética
de máquina. No se interpreta un cambio de signo aislado como prueba suficiente
de una raíz en expresiones como `1/x` o `tan(x)` alrededor de sus asíntotas.

La curva utiliza hasta 801 muestras y corta los segmentos cuyo dominio no puede
comprobarse. Puede omitir oscilaciones rápidas y raíces tangenciales; no garantiza
encontrar todas las raíces. No se incluye sugerencia automática de intervalos.
Sin JavaScript funcionan el formulario, el resultado, la verificación y la tabla.

## Plotly y empaquetado

Se versionan el bundle **basic** de Plotly.js **4.1.2**, su traducción española y
la licencia MIT sin modificar, en `static/calculadora/vendor/`. Procedencia:
[distribuciones oficiales](https://github.com/plotly/plotly.js/blob/v4.1.2/dist/README.md),
[licencia](https://github.com/plotly/plotly.js/blob/v4.1.2/LICENSE) y
[API de actualización](https://plotly.com/javascript/plotlyjs-function-reference/).
Las plantillas cargan archivos locales y no consultan CDNs durante el uso.
`tests/test_biseccion_assets.py` fija sus SHA-256 y comprueba el `.spec`.
PyInstaller incluye el árbol estático completo y las importaciones del módulo.
No se cambia la versión ni se prepara una release.

## Lectura decimal y errores de dominio

El selector **Decimales visibles** cambia solo la lectura de los resultados
almacenados, sin peticiones ni nuevas iteraciones. Parte de seis decimales y
permite disminuir o aumentar (4, 6, 8, 12, 16), o ver **Precisión completa**.
Siempre se usa escritura decimal, sin notación científica. Solo el valor que lo
necesita gana cifras: un número no nulo nunca parece cero, y a, b y c de una misma
fila no se confunden; véase [la interfaz compartida](newton-raphson.md#zona-de-estudio-compartida).
`≈` señala valores redondeados y el título conserva el valor almacenado; en móvil
puedes elegir precisión completa. Completa significa valor de máquina, no
exactitud matemática. Sin JavaScript se conserva la lectura completa.

Los errores indican qué condición impide trabajar en números reales: √ exige
contenido no negativo, los logaritmos contenido positivo y un denominador no
puede anularse. Para √(x) con a negativo se puede justificar a ≥ 0; para ln(x)
con a no positivo, a > 0. En expresiones compuestas solo se recuerda la condición
sobre el argumento: no se inventa un intervalo corregido ni se promete que el
nuevo intervalo contenga una raíz. Las cotas conservadoras pueden rechazar un
intervalo válido si no logran verificar esa condición.

π inserta π (alias de pi), e inserta e. ln es logaritmo natural, de base e;
log₁₀ inserta log10(), de base 10. log() sigue siendo alias del natural.

El teclado compartido conserva el campo de inserción, la selección y el modo
superíndice mientras se desplazan sus grupos. La barra y los gestos táctiles usan
el scroll nativo; la rueda vertical desplaza horizontalmente cuando hay espacio
y vuelve a dejar desplazar la página al llegar al borde. Se conserva Deshacer.
