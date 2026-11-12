# Regla falsa

[Índice](README.md) · [Bisección](biseccion.md) · [Pruebas](pruebas.md)

Disponible en **Métodos numéricos → Raíces de ecuaciones → Método de regla falsa**,
en `/metodos-numericos/regla-falsa/`, con recursos locales en navegador y escritorio.

## Uso y recorrido

Escribe una función para ver su gráfica antes de elegir extremos. El teclado,
la sintaxis y las herramientas de exploración son los mismos de [Bisección](biseccion.md#uso).
Selecciona a y b en la curva, arrastra sus líneas o escribe los valores; después
pulsa **Resolver por regla falsa**. La tolerancia predeterminada es `0.0001`,
positiva y reducible; el máximo es 200 iteraciones, configurable entre 1 y 1000.
El campo HTTP `precision` se conserva en ambos métodos, pero aquí se etiqueta
**Tolerancia del error absoluto**.

La gráfica dibuja la secante entre `(a,f(a))` y `(b,f(b))`, su corte `(xr,0)`
y el segmento hasta `(xr,f(xr))`. La franja representa el intervalo anterior a
la sustitución. Anterior/Siguiente, el deslizador y las filas del procedimiento
recorren el mismo JSON sin recalcular ni pedir muestras. Cada paso explica los
signos, el extremo sustituido, el extremo fijo, Ea y el motivo para seguir o parar.
El primer paso no inventa un error: falta una aproximación anterior.

El resultado, la tabla y la verificación funcionan sin JavaScript. Estudio y
Minimalista conservan el mismo cálculo; el panel didáctico pasa debajo de la gráfica
en pantallas estrechas. El selector de decimales cambia solo la lectura y evita
confundir valores distintos o mostrar ceros falsos.

El historial de la sesión agrupa los intervalos probados con la misma función, con
su estado, aproximación, iteraciones y residuo. Un resultado sin convergencia nunca
se presenta como una raíz confirmada. La gráfica muestra la secante, su corte xr, la
subida hasta f(xr), el intervalo de la iteración (franja clara) y el actualizado
(franja intensa); véase [la interfaz compartida](newton-raphson.md#zona-de-estudio-compartida).

## Algoritmo y criterio de parada

Se implementa **regla falsa clásica**, sin alternarla con bisección ni modificar
los valores de la función para acelerar la convergencia:

1. Validar extremos finitos, `a < b`, tolerancia y máximo de iteraciones.
2. Comprobar dominio y continuidad con la envolvente conservadora de `FuncionReal`.
3. Atender un cero en los extremos; en otro caso exigir signos opuestos sin multiplicarlos.
4. Calcular `xr = (a·f(b) − b·f(a)) / (f(b) − f(a))`, equivalente a
   `b − f(b)·(a − b)/(f(a) − f(b))`, y evaluar `f(xr)`.
5. Si da cero, terminar como cero calculado. En otro caso, sustituir el extremo
   cuya evaluación tiene el mismo signo y conservar el cambio de signo.
6. Calcular `Ea = |xr actual − xr anterior|`, si existe una aproximación anterior.
7. Cuando `Ea ≤ tolerancia`, evaluar un punto de prueba hacia el otro extremo,
   a no más de una tolerancia de xr y dentro del intervalo. Solo declarar
   convergencia si da cero o tiene signo contrario a f(xr).
8. Recalcular f(xr) al preparar el resultado. Informar sin convergencia si se
   agotan las iteraciones o la secante redondeada ya no produce un punto interior.

Ea es un **error absoluto aproximado**: mide el cambio entre iteraciones. No es
el error absoluto verdadero `|raíz − xr|` ni el residuo `|f(xr)|`.
Ea o un residuo pequeños por sí solos no justifican convergencia. La cota se
obtiene del tramo confirmado mediante signos, bajo las comprobaciones de
continuidad y la precisión de máquina. No encontrar ese cambio de signo tampoco
demuestra que no haya raíces cercanas: podría haber varias entre los puntos.

| Estado | Interpretación |
| --- | --- |
| `exacta` | f(xr) da cero en aritmética de máquina; no demuestra error matemático exactamente cero. |
| `tolerancia` | Ea cumple y el punto de prueba confirma una raíz a distancia no mayor que la tolerancia. |
| `estancamiento` | Se agotaron las iteraciones con Ea pequeño, sin confirmación cercana. |
| `limite` | Se agotaron las iteraciones sin cumplir Ea. |
| `maquina` | El xr redondeado coincide con un extremo: no hay una nueva aproximación interior. |

La secante se interpola usando `Fraction` sobre los cuatro valores de máquina y
se convierte a float al final. Esto evita desbordar productos/restas, perder
productos subnormales o cancelar un corte pequeño al restarlo de un extremo grande.
No vuelve exacta la evaluación de f. La biblioteca estándar conserva exactamente
el valor binario al [convertir un float a Fraction](https://docs.python.org/3.13/library/fractions.html).

Si sumar la tolerancia redondea el punto de prueba demasiado lejos, se ajusta un
valor representable hacia xr con [math.nextafter](https://docs.python.org/3.13/library/math.html#math.nextafter).
La distancia se compara como racional para no aceptar un exceso oculto por
redondeo; la cota devuelta redondea hacia fuera, sin superar la tolerancia.
Si no existe un punto distinto suficientemente cercano, no se confirma convergencia.

La envolvente de dominio puede rechazar intervalos válidos cuando no consigue
certificarlos. Una curva de 801 muestras puede omitir oscilaciones o raíces
tangenciales. Ni la gráfica ni este método aseguran encontrar todas las raíces.

## Ejemplos reproducibles

Con tolerancia `0.0001`:

| Función e intervalo | Iteraciones | xr aproximado | Ea aproximado | Estado |
| --- | ---: | ---: | ---: | --- |
| `x²−2`, [1, 2] | 6 | 1.4142011834319528 | 0.000059769291 | tolerancia |
| `x⁴−5x³+0.5x²−11x+10`, [0.55, 1.1] | 5 | 0.7639219773184611 | 0.000064304877 | tolerancia |
| Mismo polinomio, [5, 5.5] | 5 | 5.236057544785505 | 0.000068483694 | tolerancia |
| Mismo polinomio, [5.2, 5.3] | 3 | 5.236066495558506 | 0.000041654654 | tolerancia |
| `1e-200*(x^20−1)`, [0, 2] | 200 | 0.00038143353095164824 | 0.000001906987 | estancamiento |

En el último ejemplo la raíz positiva es 1, muy lejos de xr pese al Ea y residuo
pequeños. En `x²−2` el extremo b queda fijo en 2: la longitud del intervalo sigue
siendo grande, aunque xr ya satisface la tolerancia mediante la confirmación local.

## Código y pruebas

- [backend/regla_falsa.py](../backend/regla_falsa.py): ciclo y confirmación.
- [backend/metodos_cerrados.py](../backend/metodos_cerrados.py): validación común.
- [Arquitectura](arquitectura.md#catálogo-y-presentación): piezas compartidas con Bisección.
- `tests.test_regla_falsa` y `tests.test_regla_falsa_web`: invariantes, casos extremos,
  estados, validación HTTP, muestras y contenido sin JavaScript.
- `uv run --locked python -m tests.regla_falsa_browser`: abrir
  `http://127.0.0.1:8897/__pruebas/` para los flujos reales de DOM y Plotly.
- Ejecutar también Bisección, teclado, catálogo, recursos, documentación y la suite
  completa siguiendo [Pruebas](pruebas.md). No se añaden dependencias ni se cambia la versión.
