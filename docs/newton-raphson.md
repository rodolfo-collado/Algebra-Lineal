# Newton-Raphson

[Índice](README.md) · [Bisección](biseccion.md) · [Regla falsa](regla-falsa.md)

Abre **Métodos numéricos → Raíces de ecuaciones → Método de Newton-Raphson**.
Introduce f(x) y x₀. Mientras escribes f(x), f′(x) aparece bajo el campo sin
resolver nada. La gráfica puede explorarse antes de resolver y permite elegir x₀
sobre la curva.

## Derivación y dominio

El backend deriva el árbol de `FuncionReal` con las reglas de suma, producto,
cociente, potencia constante y cadena. Admite las funciones del parser, entre
ellas sen, cos, tan, ln, log₁₀, exp, √ y valor absoluto. Valida la función
original al evaluar la derivada para conservar su dominio. Por ejemplo, para
`ln(2x) + x² − sen(x)` muestra `1 / x + 2 · x − cos(x)`, con x > 0.

Un punto donde la derivada no se pueda evaluar detiene el cálculo. Esto incluye
la cúspide de `abs(x)` en cero y la pendiente no finita de `√(x)` en cero.
Algunas composiciones con singularidades removibles en la fórmula de la
derivada requieren una simplificación adicional. Las potencias con exponente
dependiente de x quedan fuera de la sintaxis de `FuncionReal`.

## Algoritmo y parada

1. Evaluar f(x₀). Si da cero en aritmética de máquina, devolver x₀.
2. Evaluar f′(xₙ) y calcular xₙ₊₁ = xₙ − f(xₙ)/f′(xₙ).
3. Evaluar f(xₙ₊₁) y registrar el cambio absoluto y el residuo.
4. Detenerse ante un cero calculado o cuando tanto |xₙ₊₁ − xₙ| como
   |f(xₙ₊₁)| cumplan la tolerancia. Un punto repetido con residuo distinto
   de cero produce estancamiento o ciclo antes de aceptar la tolerancia.
5. Reevaluar f en la aproximación final válida.

La tolerancia predeterminada y máxima es 0.0001 y se puede reducir. El límite
predeterminado es 200 iteraciones, configurable entre 1 y 1000. La actualización
opera con racionales sobre los valores de máquina y se convierte a float al
final. El redondeo de lectura se aplica después del cálculo.

Las diapositivas 8 y 10–16 de *Solución numérica de ecuaciones. Métodos abiertos*
describen la fórmula, la tangente y las comprobaciones. Con f(x) = x³ − x − 2
y x₀ = 1.5, f(x₀) = −0.125, f′(x₀) = 5.75 y x₁ ≈ 1.5217391304347827.
El recorrido une (1.5, −0.125) con (x₁, 0) y después muestra (x₁, f(x₁)).
La raíz aproximada es 1.5213797068.

Newton depende del punto inicial y del comportamiento de la función. Un salto
fuera del dominio, una derivada nula o un salto no finito pueden detenerlo.
Las oscilaciones sin repetición exacta y la divergencia finita pueden alcanzar
el límite de iteraciones. El cambio y el residuo miden magnitudes distintas,
y el criterio numérico carece de una cota garantizada de distancia a la raíz.

## Zona de estudio compartida

Los tres métodos usan la misma composición. La entrada agrupa función, parámetros y
**Resolver** en una fila cuando el ancho lo permite. El veredicto encabeza el
resultado con un tono proporcional: verde para una raíz aproximada, ámbar sin
convergencia y neutro para «no aplicable» o «ausencia de raíces demostrada». Ninguna
condición matemática se presenta como error de la aplicación.

Debajo, la gráfica y la explicación breve del paso activo comparten una fila en
escritorio; la tabla tiene una fila por iteración y desplazamiento propio, para verse
junto a la gráfica. El reproductor ofrece Reiniciar, Anterior, Reproducir/Pausar,
Siguiente, barra de progreso y velocidades 0.5×, 1×, 2× y 4×. Empieza en pausa en la
primera iteración. Al terminar, cambiar los datos, enviar otro cálculo u ocultar la
pestaña, se detiene. Un clic en una fila la selecciona; con el foco en la tabla, las
flechas, Inicio, Fin, RePág y AvPág recorren las filas sin desplazar la página. Todo
usa el JSON calculado: recorrer no vuelve a calcular ni pide muestras.

Durante la reproducción la explicación no se anuncia en cada paso; en pausa vuelve
a ser una región `aria-live`. No hay animaciones: cada paso es un cambio discreto,
también con movimiento reducido. La rueda sobre la gráfica acerca o aleja, salvo si
la página ya se estaba desplazando y la gráfica pasa bajo el cursor. Arrastrar
desplaza la vista. **Vista inicial** vuelve a `[-10, 10]`; **Enfocar intervalo** o
**Enfocar tangente** encuadra el paso activo. Cambiar de iteración respeta el zoom.

El **Historial de esta sesión** aparece desde la segunda ejecución del método en la
pestaña. Guarda hasta 12 en `sessionStorage` y agrupa por función equivalente, sin
mezclar métodos. **Ver** vuelve a enviar los datos de una ejecución y la marca como
actual sin duplicarla. Sin JavaScript se muestran el veredicto, la tabla completa,
el procedimiento y la verificación.

Con Newton, el endpoint `grafica/` añade `derivada` a las muestras: el texto de
`DerivadaReal` con exponentes enteros en superíndice, o `null` si no se puede derivar.
Así f′(x) llega con la misma petición, con espera de 300 ms tras escribir y sin un
motor simbólico en JavaScript. Una función incompleta devuelve el error de
validación habitual, sin `derivada`.

## Contrato de datos de los métodos de raíces

El backend devuelve diccionarios serializables. En la página, `datos-raices`
publica `metodo`, `funcion`, `clave`, `clasificacion` y `resultado`. La función
es el texto original y la clave identifica el árbol del parser. Los resultados
válidos incluyen `estado` (motivo de parada), `mensaje`, `convergio`, `residuo`,
`max_iteraciones` e `iteraciones`. Los valores no disponibles se representan con
`null`. Las entradas inválidas producen errores de validación y `resultado: null`.

| Clasificación | Cuándo se emite |
| --- | --- |
| `entrada_invalida` | Falta un campo o la sintaxis, el orden de los extremos o los ajustes son inválidos. |
| `no_aplicable` | El dominio o las condiciones del método impiden comenzar con los parámetros dados. |
| `raiz_aproximada` | Cero calculado o criterio de convergencia satisfecho. |
| `sin_convergencia` | El cálculo se detuvo sin satisfacer el criterio. |
| `sin_raices_demostrado` | Una prueba de signo estricto excluye el cero en todo el intervalo. |
| `exploracion_no_concluyente` | La gráfica no detectó indicios en sus muestras. |
| `indicios_numericos` | La gráfica detectó ceros de máquina o cambios de signo entre muestras válidas consecutivas. |

En Bisección y Regla Falsa, `sin_cambio_de_signo` detiene el algoritmo y deja
vacía la aproximación. La prueba simbólica de signo usa reglas conservadoras
sobre el árbol. Por ejemplo, x² ≥ 0 y 1 > 0 demuestran que x² + 1 > 0 en
[−1, 1]. Para x² en [−1, 1] y x² − 1 en [−2, 2], se informa que el método
no es aplicable con esos extremos. El endpoint `grafica/` conserva `x` e `y` y
publica el número de muestras válidas, ceros calculados y cambios de signo en
`evidencia`. Esos conteos describen la exploración.

- **Newton-Raphson.** `derivada`, `x0`, `tolerancia`, `x`, `fx` y
  `error_absoluto`. Cada fila contiene `xn`, `fxn`, `dfxn`, `siguiente`,
  `fsiguiente`, `residuo` y `error_absoluto`. La tangente queda definida por
  (xn, fxn), la pendiente dfxn y el corte (siguiente, 0).
  `intento_final` guarda los valores disponibles de un paso que no se completó.
- **Bisección.** `inicial` contiene a, b, f(a) y f(b). Cada fila registra
  los extremos y sus evaluaciones, el punto medio (c, fc), el error relativo
  aproximado y el intervalo siguiente. El resultado contiene el intervalo
  final, `c`, `fc` y `precision`.
- **Regla Falsa.** `inicial` también contiene a, b, f(a) y f(b). Cada fila
  guarda los puntos de la secante (a, fa) y (b, fb), su corte (xr, 0),
  f(xr), el intervalo siguiente y los datos de confirmación de cercanía.
  El resultado conserva `xr`, `fxr`, `tolerancia` y la cota cuando se confirmó.

Las filas conservan el orden de cálculo y los valores de máquina. La tabla y
la gráfica existente leen los mismos datos. Los tres runners DOM y las pruebas
Python se describen en [Pruebas](pruebas.md).
