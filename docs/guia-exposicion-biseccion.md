# Guía breve para exponer bisección en PyGebra

## 1. La idea que quiero explicar

«La bisección sirve para aproximar una raíz: un valor de x donde f(x) vale cero.
Partimos de un intervalo que encierra al menos una raíz y lo dividimos por la
mitad repetidamente. En cada paso conservamos la mitad que sigue encerrándola».

Para aplicar el método necesitamos `a < b`, una función continua en todo el
intervalo y signos opuestos en `f(a)` y `f(b)`. Esto asegura al menos una raíz,
pero no necesariamente una sola. Si un extremo ya da cero, terminamos allí.
Un cambio de signo sin continuidad no basta: `1/x` cambia de signo alrededor
de cero, pero allí tiene una discontinuidad, no una raíz.

## 2. Cómo hacemos cada paso

Calculamos el punto medio; después `fc = funcion(c)` evalúa la función. Esta línea está en
`biseccion()` de [backend/biseccion.py](../backend/biseccion.py):

```python
        c = a + (b - a) / 2
```

`a + (b-a)/2` es matemáticamente igual a `(a+b)/2`. Evita sumar dos extremos
grandes del mismo signo, cuya suma podría exceder lo representable. No soluciona
todos los desbordamientos: por eso antes comprobamos que `b-a` sea finito.
Si el redondeo ya no permite un punto intermedio, informamos estancamiento.

Si `f(c)=0`, encontramos un cero calculado. Si no, elegimos la mitad:

```python
        elif (fa < 0) != (fc < 0):
            b, fb = c, fc
        else:
            a, fa = c, fc
```

«Si f(a) y f(c) tienen signos distintos, conservo [a,c] y reemplazo b. Si tienen
el mismo signo, conservo [c,b] y reemplazo a». Guardamos también el valor de
la función del nuevo extremo. Comparamos signos sin multiplicarlos, para evitar
desbordar con un producto muy grande.

La precisión predeterminada es `0.0001`; solo aceptamos valores positivos iguales
o menores. Siguiendo la diapositiva 3, paramos cuando la **longitud después del
recorte** cumple `b-a < precision`. No usamos el porcentaje como criterio de parada.

El error relativo entre aproximaciones es `|(c actual − c anterior)/c actual| × 100`.
No es el error verdadero respecto a una raíz conocida. El código lo calcula así:

```python
        error = abs((c - anterior) / c) * 100 if anterior is not None and c != 0 else None
```

En la primera iteración no hay anterior; si c es cero tampoco se puede dividir.
En esos casos mostramos «No definido», nunca un cero inventado.

## 3. El ejemplo del profesor

Introduzco `x^4 - 5x^3 + 0.5x^2 - 11x + 10`, intervalo `[0.55,1.1]` y precisión
`0.0001`. Al inicio, `f(0.55) ≈ 3.36088125` y `f(1.1) ≈ -6.6859`.

| Paso | c | f(c), aprox. | Mitad que conservamos |
|---|---:|---:|---|
| 1 | 0.825 | -1.079015 | [0.55, 0.825] |
| 2 | 0.6875 | 1.272476 | [0.6875, 0.825] |
| 3 | 0.75625 | 0.131743 | [0.75625, 0.825] |

En el paso 2, el error relativo es `|(.6875-.825)/.6875|×100 = 20 %`.
Después de **13 iteraciones**, obtenemos `c ≈ 0.763970947265625` y longitud
restante `0.000067138671875`, menor que `0.0001`.

**¿Por qué converge si f(c) ≈ -0.000669776 y no es cero?** Porque la precisión
pedida corresponde al eje x, no al valor de la función. Conservamos un intervalo
con una raíz y lo reducimos suficientemente. El último c queda en un extremo
del intervalo final: su distancia a una raíz no supera esa longitud, bajo las
comprobaciones realizadas y la precisión de máquina. El residuo f(c) se verifica
otra vez y se muestra aparte. Usamos las diapositivas 3 y 6; recalculamos las
evaluaciones porque la guía PDF y la última fila de la diapositiva tienen discrepancias.

## 4. Cómo se conecta el programa

La ruta web llega a `resolver_biseccion()` en
[views_raices.py](../frontend/web/calculadora/views_raices.py).
`BiseccionForm`, en [forms_raices.py](../frontend/web/calculadora/forms_raices.py),
valida los campos y construye `FuncionReal`. Esta clase, en
[funciones_reales.py](../backend/funciones_reales.py), convierte la expresión en
un árbol de operaciones permitido. `explicitar_productos()` transforma `5x` en
un producto antes de analizarlo; `sen(x)` se interpreta igual que `sin(x)`. No usamos
`eval` ni ejecutamos código escrito por el usuario.

La vista llama a `biseccion()`, que devuelve resultado, estado e iteraciones.
La plantilla [index.html](../frontend/web/calculadora/templates/calculadora/modules/biseccion/index.html)
presenta esos datos y los publica como JSON para JavaScript. El algoritmo vive
en Python; la plantilla y Plotly no resuelven la raíz. Hay límites de expresión
e iteraciones y comprobaciones de dominio, continuidad y valores finitos. Las
cotas son conservadoras: pueden rechazar una expresión válida.

## 5. Qué hace la gráfica

[servicios_raices.py](../frontend/web/calculadora/servicios_raices.py), mediante
`muestrear()`, genera hasta 801 puntos. `explorar_funcion()` entrega las muestras;
no ejecuta la bisección. En [raices.js](../frontend/web/calculadora/static/calculadora/raices.js),
`iniciar()` crea la gráfica con `Plotly.newPlot` y `mostrarPaso(i)` selecciona una
iteración ya guardada. [biseccion.js](../frontend/web/calculadora/static/calculadora/biseccion.js)
aporta los puntos y la explicación de cada paso. El controlador compartido actualiza la franja:

```javascript
        Plotly.update(grafica, { x: [puntos.x], y: [puntos.y], text: [puntos.text],
            customdata: [etiquetas(puntos.x, puntos.y, 12)], "marker.size": [puntos.size], "marker.symbol": [puntos.symbol] },
            extremos.length === 2 ? { "shapes[2].x0": p.a, "shapes[2].x1": p.b,
                "shapes[3].x0": p.nuevo_a ?? p.a, "shapes[3].x1": p.nuevo_b ?? p.b } : {}, [1])
            .finally(() => { mutando = false; });
```

Con solo la función se abre una ventana de exploración `[-10, 10]`. Los botones
**Elegir a/b** permiten elegir un punto de la curva; los campos y las líneas
permiten afinar los extremos. Esto no prueba que exista una raíz: Resolver valida
dominio, continuidad y signos de forma independiente.

Reproducir, Anterior/Siguiente, la barra de progreso y un clic o las flechas sobre una fila llaman al mismo recorrido.
La lectura identifica a, c y b, sus signos y qué mitad conservamos, separando
el intervalo antes y después del recorte. La verificación plegable explica
existencia, resta de extremos y precisión con los valores de nuestro cálculo.
El selector de decimales solo cambia la lectura: nunca vuelve a calcular. La
opción completa permite consultar los valores de máquina. ln usa base e; log₁₀
usa base 10, y el teclado también tiene π y e.
Arrastrar las líneas a y b actualiza los campos mediante `plotly_relayout`;
para obtener otra solución debemos volver a pulsar Resolver. Editar marca el
resultado anterior como desactualizado. Plotly está guardado localmente y funciona
sin Internet. La curva muestreada ayuda a explorar; no demuestra todas las raíces.

## 6. Mi demostración y preguntas posibles

1. Empezar con los campos vacíos. Escribir la función y el intervalo del ejemplo;
   al enfocar f(x), mostrar el teclado contextual (x² inserta x² y aⁿ activa el modo superíndice para escribir el exponente).
   Resolver y señalar las 13 iteraciones.
2. Pulsar Reproducir a 1× y pausar en el tercer paso; mover la barra y señalar la fila activa.
3. Arrastrar un extremo y explicar el aviso de resultado anterior.
4. Resolver `[5,5.5]` y después `[5.2,5.3]`: requieren 13 y 10 pasos.
   Señalar en el historial las dos aproximaciones cercanas y sus iteraciones.
   El historial aparece desde la segunda ejecución y agrupa por función.

**¿Por qué no asegura una sola raíz?** Continuidad y signos opuestos aseguran
existencia; un intervalo puede contener varias. El historial tampoco prueba unicidad.

**¿Qué pasa con `1/2x`?** Se lee `(1/2)*x`, con las mismas prioridades que la
multiplicación explícita. Para otro denominador escribo `1/(2x)`. No adivinamos
nombres como `senx`; escribimos `sen(x)`. `1e-3` es un número científico y `2*e`
es multiplicación por la constante.

**¿Una biblioteca encuentra la raíz?** No: el ciclo es manual. Plotly dibuja;
las funciones de `math` evalúan operaciones, no sustituyen la bisección.

**¿Y si no alcanza la precisión?** El programa informa sin convergencia si llega
al límite de iteraciones o se estanca; los errores de dominio se explican al usuario.
