# Método de la secante

[Índice](README.md) · [Newton-Raphson](newton-raphson.md) · [Bisección](biseccion.md) · [Regla falsa](regla-falsa.md)

Abre **Métodos numéricos → Raíces de ecuaciones → Métodos abiertos** y elige
**Secante** en el selector de método. Introduce f(x), x₀ y x₁. La gráfica aparece
mientras escribes f(x), antes de resolver, y permite elegir x₀ y x₁ sobre la curva
(«Elegir x₀», «Elegir x₁») o arrastrar sus líneas.

## Métodos abiertos

Newton-Raphson y Secante forman una sola herramienta del catálogo, **Métodos
abiertos**: un único lugar en la navegación, el buscador y el Inicio. Dentro, un
selector segmentado cambia de método. Cada método conserva su ruta, su formulario,
su explicación y su historial:

| Método | Ruta | Puntos iniciales |
| --- | --- | --- |
| Newton-Raphson | `/metodos-numericos/metodos-abiertos/newton-raphson/` | x₀ (tangente, con f′ automática) |
| Secante | `/metodos-numericos/metodos-abiertos/secante/` | x₀ y x₁ (recta secante, sin derivada) |

Cambiar de método conserva la función escrita: el enlace del selector la lleva como
`?funcion=…` y el otro formulario la recibe ya escrita. Nunca se trasladan puntos
iniciales ni resultados, así que los estados no se mezclan. La ruta antigua
`/metodos-numericos/newton-raphson/` (y su `grafica/`) redirige a la nueva: GET con
301 y conservando la consulta; POST con 308, que reenvía el mismo cuerpo.

## Algoritmo y parada

La fórmula de la diapositiva 20 es una fracción completa:

xₙ₊₁ = xₙ − f(xₙ) · (xₙ − xₙ₋₁) / [f(xₙ) − f(xₙ₋₁)]

`backend/secante.py` la implementa de forma explícita, sin bibliotecas que resuelvan
el método:

1. Validar que x₀ ≠ x₁, la tolerancia (positiva y no mayor que 0.0001) y el máximo
   de iteraciones (1 a 1000, 200 por defecto).
2. Evaluar f(x₀) y f(x₁). Si una cae fuera del dominio, el método no es aplicable
   con esos puntos. Si alguna vale cero en aritmética de máquina, ese punto es la raíz.
3. Calcular numerador f(xₙ)·(xₙ − xₙ₋₁) y denominador f(xₙ) − f(xₙ₋₁) con racionales
   exactos sobre los valores de máquina, y la nueva aproximación xₙ₊₁.
4. Evaluar f(xₙ₊₁) y registrar el cambio |xₙ₊₁ − xₙ| y el residuo |f(xₙ₊₁)|.
5. Desplazar los puntos: xₙ₋₁ ← xₙ y xₙ ← xₙ₊₁ (diapositiva 21).
6. Detenerse con f(x) = 0 o cuando **el cambio y el residuo** cumplan la tolerancia.
   Un cambio pequeño con residuo grande no es convergencia: con
   f(x) = 10⁶(x³ − x − 2), la iteración 6 tiene cambio 3.4·10⁻⁶ y residuo 0.007, y
   el método sigue hasta la 7.

No exige cambio de signo ni orden: x₀ y x₁ no son extremos de un intervalo y pueden
estar al mismo lado de la raíz o en orden descendente. Por eso tampoco conserva un
intervalo que encierre la raíz (diapositiva 24).

| Estado | Cuándo | Clasificación |
| --- | --- | --- |
| `tolerancia` | Cambio y residuo cumplen la tolerancia. | Raíz aproximada |
| `exacta` | f(x) = 0 en aritmética de máquina (también x₀ o x₁). | Raíz aproximada |
| `denominador` | f(xₙ) − f(xₙ₋₁) = 0: la secante es horizontal. | No aplicable en la primera iteración; sin convergencia después |
| `denominador_pequeno` | El denominador es menor que 10⁻¹² · max(\|f(xₙ)\|, \|f(xₙ₋₁)\|): la pendiente queda dominada por el redondeo. | Igual que `denominador` |
| `dominio_inicial` | f(x₀) o f(x₁) no se puede evaluar. | No aplicable |
| `dominio` | El corte cae fuera del dominio o da un valor no finito. | Sin convergencia; se conserva la última aproximación válida |
| `divergencia` | El salto excede el rango de máquina. | Sin convergencia |
| `estancamiento` / `oscilacion` | La máquina repite la aproximación o vuelve a una anterior. | Sin convergencia |
| `limite` | Se alcanzó el máximo de iteraciones. | Sin convergencia |

## Ejemplos de clase

Ambos están en **Ejemplos** del formulario:

- **Diapositivas 22 y 23:** f(x) = x³ − x − 2, x₀ = 1, x₁ = 2. f(1) = −2, f(2) = 4 y
  x₂ = 2 − [4(2 − 1)] / [4 − (−2)] = 2 − 4/6 ≈ 1.333333333. Las seis
  iteraciones coinciden con la tabla de la diapositiva 23 redondeada a seis decimales
  (1.333333, 1.462687, 1.531169, 1.520926, 1.521376, 1.521380); la raíz es
  aproximadamente 1.521379707.
- **Práctica integradora:** f(x) = x³ − 2x − 5, x₀ = 2, x₁ = 3, tolerancia 10⁻⁶;
  converge a 2.0945514815 en seis iteraciones. Cargar otro ejemplo restablece la
  tolerancia a 0.0001.

## Zona de estudio

La composición es la de Newton-Raphson. En escritorio, la columna izquierda tiene la
gráfica y, debajo, la tabla; la derecha, la fórmula general, la sustitución y la
explicación del paso activo: las tres se consultan a la vez. Por debajo de 44rem de
ancho el orden es gráfica, explicación y tabla.

**Gráfica (diapositiva 19).** Cada iteración muestra Pₙ₋₁ = (xₙ₋₁, f(xₙ₋₁)) y
Pₙ = (xₙ, f(xₙ)), la recta secante punteada que pasa por ambos y se prolonga hasta
el eje x, el corte xₙ₊₁ (rombo) y su altura f(xₙ₊₁). Los rótulos P y xₙ₊₁ son
anotaciones de Plotly: los textos de una traza de varios puntos no siempre se
redibujan al actualizarla paso a paso. **Enfocar secante** encuadra los tres puntos
del paso activo. Newton conserva sus tangentes.

**Explicación (diapositivas 20–22).** Un bloque fijo muestra f(x) en notación de clase
y la fórmula como fracción apilada. Para cada iteración:

1. los puntos Pₙ₋₁ y Pₙ con sus evaluaciones;
2. la sustitución con símbolos y con números, con paréntesis en los negativos:
   x₂ = 2 − 4 · (2 − 1) / (4 − (−2));
3. las operaciones: numerador y denominador ya calculados (4/6) y la nueva
   aproximación destacada;
4. la comprobación del error absoluto y del residuo frente a la tolerancia, con
   «cumple» o «no cumple» escrito;
5. la actualización de los puntos o el motivo de parada.

Si una igualdad no cabe, la fracción baja entera bajo su prefijo; nunca se parte por
dentro. Los lectores de pantalla reciben la forma lineal.

**Tabla (diapositiva 23).** n, xₙ₋₁ (anterior), xₙ (actual), xₙ₊₁ (nueva),
|xₙ₊₁ − xₙ| (cambio) y |f(xₙ₊₁)| (residuo). Una fila, el deslizador, Anterior,
Siguiente o Reproducir actualizan tabla, gráfica y explicación a la vez, con los
datos ya calculados: recorrer no recalcula ni pide muestras. Los números siguen el
selector **Decimales** con precisión interna completa.

El historial de la sesión agrupa por función y compara pares (x₀, x₁); es propio de
Secante (`pygebra-raices-historial-secante`).

## Contrato de datos

`secante()` devuelve `x0`, `x1`, `x`, `fx`, `residuo`, `error_absoluto`, `tolerancia`,
`max_iteraciones`, `estado`, `mensaje`, `convergio`, `clasificacion`, `iteraciones` e
`intento_final`. Cada fila contiene `i`, `anterior`, `fanterior`, `actual`, `factual`,
`numerador`, `denominador`, `siguiente`, `fsiguiente`, `residuo` y `error_absoluto`.
`numerador` y `denominador` son solo de lectura y valen `null` si no caben en un
float. `intento_final` guarda el paso que no se completó (por ejemplo, con el
denominador nulo).

## Componentes compartidos

- `views_raices._resolver_abierto`: formulario, cálculo, encuadre inicial y
  `?funcion=` para Newton y Secante.
- `modules/raices/metodos_abiertos.html`: el selector; `base.html` expone los bloques
  `selector_metodo` y `accion_ruta` (Secante envía a su propia ruta).
- `metodos_abiertos.js`: valores, fracciones, igualdades, comprobación, ejemplos
  (`data-ejemplo`) y conservación de la función. `newton_raphson.js` y `secante.js`
  solo aportan su geometría y su lectura.
- `raices.js` distingue intervalos (a, b con franjas) de puntos iniciales (x₀, x₁ sin
  franjas) y dibuja las anotaciones `rotulos` de cada paso.
- Las clases `abierto-*` de `raices.css` sustituyen a las antiguas `newton-*`.

## Limitaciones

La convergencia depende de x₀, x₁ y del comportamiento de f. Cambio y residuo no son
el error verdadero |x − raíz| ni ofrecen una cota garantizada. El umbral del
denominador casi nulo es heurístico. La gráfica es un muestreo y puede omitir
detalles. En pantallas estrechas la tabla de seis columnas se desplaza en horizontal dentro
de su marco, sin desbordar la página. Véanse también las [Pruebas](pruebas.md).
