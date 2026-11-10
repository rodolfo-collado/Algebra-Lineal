# Newton-Raphson

[Índice](README.md) · [Bisección](biseccion.md) · [Regla falsa](regla-falsa.md)

Disponible en **Métodos numéricos → Raíces de ecuaciones → Método de Newton-Raphson**,
`/metodos-numericos/newton-raphson/`. No requiere servicios externos.

## Entrada y exploración

Escribe f(x), su derivada manual f′(x) y x₀. Ambas expresiones utilizan `FuncionReal`
y el teclado matemático existente: potencias, productos implícitos, sen, ln, √, etc.
La derivada debe corresponder a la función: no se calcula ni se comprueba simbólicamente.
La gráfica de f(x) puede explorarse sin escribir la derivada ni resolver.
Selecciona x₀ sobre la curva, arrastra su línea o escríbelo. Los ejemplos están plegados.

La tolerancia predeterminada y máxima es **0.0001**; admite cualquier valor positivo
menor representable. El máximo de iteraciones es 200, configurable entre 1 y 1000.
La misma tolerancia se aplica por separado al cambio absoluto en x y al residuo en f(x).
Estas cantidades tienen escalas distintas: cambiar la escala de f cambia su residuo.

## Algoritmo y criterio de parada

1. Validar punto inicial, tolerancia, máximo y evaluación de f(x₀).
2. Si f(x₀) da cero, devolverlo sin actualizaciones, incluso si su derivada es cero.
3. Evaluar la derivada manual en x actual. Si es cero, no dividir.
4. Calcular explícitamente `x siguiente = x actual − f(x actual)/f′(x actual)`.
5. Evaluar f(x siguiente), registrar la tangente, el residuo siguiente y el cambio absoluto.
6. Detenerse ante un cero calculado; en otro caso exigir **ambos**
   `|x siguiente − x actual| ≤ tolerancia` y `|f(x siguiente)| ≤ tolerancia`.
7. Una repetición exacta o un ciclo se detiene sin éxito, antes de aceptar tolerancia.
8. Repetir hasta el límite; reevaluar f(x) independientemente al construir el resultado.

El cambio es un error absoluto **aproximado**, no el error verdadero `|x − raíz|`.
Newton no conserva un intervalo que encierre una raíz ni demuestra una cota de distancia.
Cumplir las dos condiciones es un criterio numérico, no una prueba de existencia o unicidad.
Un cero de máquina tampoco demuestra un cero matemático exacto.

No se fija un umbral absoluto arbitrario para pendientes pequeñas: una función escalada
puede tener una pendiente pequeña perfectamente útil. La actualización se calcula con
`Fraction` sobre los valores binarios de máquina y se convierte a float al final, siguiendo
el patrón de Regla falsa. Si el salto o el cambio no son finitos, se detiene sin convergencia.
Esto evita desbordamientos intermedios, sin volver exacta la evaluación de las expresiones.

| Estado | Significado |
| --- | --- |
| exacta | Cero calculado, en el punto inicial o tras una actualización. |
| tolerancia | Residuo y cambio cumplen; no es una cota de distancia a la raíz. |
| derivada | Derivada cero con residuo distinto de cero. |
| dominio | La derivada o la siguiente evaluación no son válidas; conserva el último punto válido. |
| divergencia | El salto o el cambio exceden el rango finito de máquina. |
| oscilacion | Una aproximación repite exactamente otra anterior. |
| estancamiento | La actualización redondea al mismo punto sin dar cero. |
| limite | No se satisfacen las condiciones al agotar las iteraciones. |

El punto inicial fuera del dominio es un error de entrada. Si un salto posterior sale del
dominio, no se añade una fila incompleta. Las oscilaciones sin repetición exacta y la
divergencia que permanece finita pueden alcanzar `limite`; no se diagnostican por un
umbral de tamaño arbitrario. No se sustituyen pasos por bisección ni se modifica el algoritmo.

## Geometría y recorrido

Cada fila conserva `(xn, f(xn))`, la pendiente manual, el corte `(x siguiente, 0)`
y el siguiente punto de la curva. El segmento de tangente une el punto actual con
el corte; un segmento vertical muestra la nueva evaluación. Si la derivada manual
es incorrecta, la recta dibujada no será la tangente real de f: revisa la expresión.

Anterior/Siguiente, deslizador y foco/clic sobre las filas recorren el mismo JSON,
sin recalcular ni solicitar muestras. **Ver tangente de este paso** encuadra los dos
puntos en x y vuelve a muestrear; zoom, desplazamiento y Vista inicial siguen disponibles.
El panel permanece junto a la curva en escritorio y debajo en pantallas estrechas.
Estudio/Minimalista y día/noche utilizan los mismos tokens y componentes compartidos.
El resultado, procedimiento y verificación también funcionan sin JavaScript.

## Referencias y pruebas

Con tolerancia 0.0001, `x²−2`, `2x`, x₀=1.5 aproxima √2;
`x³−x−2`, `3x²−1`, x₀=1.5 aproxima 1.5213797068.
`x³−2x+2`, `3x²−2`, x₀=0 repite 0 → 1 → 0.
`ln(x)`, `1/x`, x₀=4 propone un salto negativo y termina por dominio.
`x²`, `2x`, x₀=0 ya es raíz; `x²−2`, `2x`, x₀=0 tiene derivada nula.

- `uv run --locked python -m unittest tests.test_newton_raphson tests.test_newton_raphson_web -v`
- `uv run --locked python -m tests.newton_raphson_browser`; abrir `http://127.0.0.1:8901/__pruebas/`.
- Ejecutar también los runners de Bisección/Regla falsa y la suite completa de [Pruebas](pruebas.md).

El runner DOM comprueba selección/arrastre mediante eventos de Plotly, geometría de cada
fila, recorrido, teclado en los dos campos, ejemplos, estados, cifras y ausencia de desborde
en 1280, 744 y 390 px, en ambos estilos y temas. Los eventos sintéticos no sustituyen
pruebas físicas de arrastre, touch o lector de pantalla.
