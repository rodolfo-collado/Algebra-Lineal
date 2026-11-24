# Jacobi y Gauss-Seidel en Ax = b

Abre **Métodos numéricos → Sistemas lineales → Métodos iterativos** e ingresa
la matriz cuadrada A y el vector b. Puedes elegir **Jacobi**, **Gauss-Seidel** o
**Comparar ambos**. La comparación parte del mismo vector inicial para los dos
métodos. Si dejas el vector inicial vacío, PyGebra usa ceros.

En **Tipo de entrada → Sistema de ecuaciones** también puedes escribir el sistema,
como en Reducción por filas y con las mismas reglas: incógnitas `x1, x2, …`,
coeficientes implícitos, fracciones, decimales con punto y términos a ambos lados
del `=`. Una variable que no aparece en una ecuación vale 0 en esa fila. Escribe
tantas ecuaciones como incógnitas y en orden: la ecuación `i` forma la fila `i` de A,
así que debe contener `xi`. El resultado es el mismo que con A y b en celdas.

**Métodos cerrados** y **Métodos abiertos** buscan raíces de funciones.
**Métodos iterativos** aproxima las componentes de la solución de un sistema
lineal. Desde **Matrices → Sistemas lineales (Ax = b)** puedes abrir la
herramienta mediante el enlace que acompaña a los métodos directos.

## Cómo se calcula

- `aᵢⱼ` es el coeficiente de la fila `i` y la columna `j` de A. `bᵢ` es el
  término independiente de esa fila y `xⱼ⁽ᵏ⁾` es la componente `j` del vector
  aproximado tras `k` iteraciones.
- El bucle exterior hace hasta el número de iteraciones solicitado. Dentro de
  cada vuelta, el bucle de filas calcula `x₁, x₂, …, xₙ` en ese orden. Las sumas
  recorren las demás columnas de la fila. Cada despeje divide por `aᵢᵢ`.
- **Jacobi** conserva el vector anterior durante toda la vuelta.
  `xᵢ⁽ᵏ⁺¹⁾ = [bᵢ − Σⱼ≠ᵢ aᵢⱼ xⱼ⁽ᵏ⁾] / aᵢᵢ`.
- **Gauss-Seidel** aprovecha las componentes nuevas a medida que las calcula.
  `xᵢ⁽ᵏ⁺¹⁾ = [bᵢ − Σⱼ<ᵢ aᵢⱼ xⱼ⁽ᵏ⁺¹⁾ − Σⱼ>ᵢ aᵢⱼ xⱼ⁽ᵏ⁾] / aᵢᵢ`.
  Así, al calcular `x₂` en el ejemplo de clase, Jacobi usa el `x₁` de la vuelta
  anterior y Gauss-Seidel usa el que acaba de obtener. Por eso aparecen
  aproximaciones distintas. Para ese sistema Gauss-Seidel converge antes.

Después de cada vuelta el motor mide el mayor cambio entre componentes
(`‖x⁽ᵏ⁺¹⁾ − x⁽ᵏ⁾‖∞`) y el mayor valor absoluto de los residuos de las ecuaciones
(`‖b − Ax⁽ᵏ⁺¹⁾‖∞`). Ambos deben ser **estrictamente menores** que la tolerancia,
como indica la diapositiva 24. La tolerancia predeterminada es `0.0001`. El cambio
mide cuánto se movió la aproximación. El residuo mide cuánto falta para cumplir las
ecuaciones. Los despejes operan en coma flotante. El motor verifica el vector
obtenido contra A y b con los números ingresados para evitar que el redondeo de
un coeficiente o un término independiente oculte un residuo. La dominancia
también se comprueba con los coeficientes de entrada. La precisión de
visualización se aplica al final.

Se admiten matrices cuadradas hasta 10 × 10 y de 1 a 500 iteraciones, con 100 de
forma predeterminada. Un cero en la diagonal impide el despeje de esa fila.
PyGebra conserva el orden ingresado, informa qué filas incumplen
`|aᵢᵢ| > Σⱼ≠ᵢ |aᵢⱼ|` y permite continuar. La dominancia estricta por filas
garantiza convergencia en aritmética exacta. Cuando se agota el límite o se supera
el rango de la aritmética de máquina, se conserva la última fila finita disponible.

## Lectura del resultado

El resultado sigue la proximidad de Newton-Raphson: veredicto, zona de estudio y,
plegadas, las comprobaciones.

- **Veredicto.** Dice si cada método converge, no converge en el límite o supera el
  rango numérico, con la última aproximación y los dos criterios frente a ε. Una línea
  informa la dominancia diagonal estricta por filas. Al comparar, una tabla reúne ambos
  métodos con las mismas condiciones (x⁽⁰⁾, ε y límite) y una gráfica superpone sus
  residuos `‖r‖∞` en escala logarítmica con la tolerancia.
- **Iteraciones paso a paso.** Una sola `k` por método sincroniza la gráfica de todas
  las incógnitas (Plotly: un color y un marcador por incógnita, leyenda interactiva y
  clic en un punto), la sustitución de esa iteración y la tabla (clic, flechas, Inicio y
  Fin). La gráfica secundaria muestra el cambio máximo y el residuo con la línea de ε.
  Al comparar, un selector alterna el método y conserva la `k` (acotada a sus
  iteraciones).
- **Sustitución.** Cada incógnita ocupa dos renglones: el despeje con superíndices
  `x⁽ᵏ⁻¹⁾`/`x⁽ᵏ⁾` y los valores sustituidos, en fracciones apiladas. El fondo neutro marca
  los valores anteriores y el color de marca los nuevos: en Jacobi todo procede de
  `x⁽ᵏ⁻¹⁾` (actualización simultánea); en Gauss-Seidel las filas se numeran por orden y
  `j < i` ya usa `x⁽ᵏ⁾`. Al señalar un valor se resalta su origen en la fila anterior o
  en la tabla.
- **Comprobaciones** (plegadas). `|aᵢᵢ|` frente a `Σⱼ≠ᵢ |aᵢⱼ|` por fila y `Ax = b` con la
  última aproximación: `(Ax)ᵢ`, `bᵢ` y `rᵢ`.

Los números de máquina usan el formato global **Exacto / Decimal**
(`presentacion_numerica.representar_flotante` y el filtro `flotante`): Exacto muestra el
decimal más corto que identifica al float almacenado; Decimal redondea a 2, 4, 6 u 8
decimales con el mismo redondeo al par, sin exponentes y sin leer como 0 un valor que
no lo es (0.0000466 con 4 decimales se lee 0.00005). Las sustituciones copian el texto de
la tabla y cambian «=» por «≈» cuando el formato redondea; las etiquetas de las gráficas
siguen el mismo formato. Nada se recalcula al cambiar de formato o de iteración.

**Copiar tabla (CSV)** pone en el portapapeles la tabla con las cifras almacenadas
(`text/plain` en CSV y una tabla HTML que las hojas de cálculo pegan por columnas). Se
usa el portapapeles y no una descarga porque la app de escritorio (pywebview) no admite
descargas (`ALLOW_DOWNLOADS` desactivado).

## Ejemplos de clase y correcciones

Los ejemplos están en el menú de edición, como en Conjuntos: clic derecho (o
Shift+F10) sobre una celda de A o b → **Cargar ejemplo · sustituye el sistema**. Sin
JavaScript aparecen en un bloque plegable. Hay tres: el ejemplo de clase, la práctica
de la diapositiva 28 y un sistema sin dominancia diagonal cuyas aproximaciones crecen.
El de clase aparece en el Word
`Ejemplos_Paso_a_Paso_Jacobi_Gauss_Seidel.docx` y la diapositiva 9 de
`Presentacion_Jacobi_Gauss_Seidel.pptx`. La solución exacta es `(1, 2, −1, 1)`.
Con los valores predeterminados se obtienen 15 iteraciones por Jacobi
(`‖r‖∞ ≈ 4.663227e−5`) y 6 por Gauss-Seidel (`‖r‖∞ ≈ 7.697313e−5`). Las
iteraciones coinciden bit a bit con el script de referencia `jacobi_gauss_seidel.py`:
Gauss-Seidel suma en el orden de las columnas, tomando `x⁽ᵏ⁾` en `j < i`.

| Fuente | Discrepancia | Valores usados en las pruebas |
| --- | --- | --- |
| Diapositiva 15, Jacobi k = 2 | Se imprimen 1.704545 para x₂ y 0.906818 para x₄. | x₂ ≈ 1.715909 y x₄ ≈ 0.885227, como en la diapositiva 16. |
| Diapositiva 20, Gauss-Seidel k = 1 | Se imprime x₄ = 0.751591. | x₄ ≈ 0.878864 a partir de `(15 − 3·2.327273 − 0.987273) / 8`. |
| Diapositiva 21, Gauss-Seidel k = 2 | Arrastra el x₄ de la diapositiva 20 y contiene otras cuentas incorrectas. | Al rehacer la vuelta con el vector correcto se obtiene (1.030182, 2.036938, −1.014456, 0.984341). |
| Word §5, Gauss-Seidel k = 2 | Algunos operandos escritos corresponden a componentes que aún no se han calculado en esa vuelta. | Para x₂ se usan x₃ ≈ −0.987273 y x₄ ≈ 0.878864 de k = 1. Para x₃ también se usa x₄ de k = 1. La tabla del Word ya trae los resultados correctos. |

La práctica de la diapositiva 28 arranca en ceros y carga un máximo de tres
iteraciones para comparar lo que pide el enunciado. Sus vectores en k = 3 son
`(1.120040, 0.695099, −0.368100, 0.577098)` con Jacobi y
`(1.130460, 0.684704, −0.355096, 0.565743)` con Gauss-Seidel, a seis
decimales. Al ampliar el límite, convergen en 11 y 5 iteraciones respectivamente.

## Verificación

```powershell
uv run --locked python -m unittest tests.test_sistemas_iterativos tests.test_sistemas_iterativos_web tests.test_presentacion_numerica -v
uv run --locked python -m tests.iterativos_browser  # http://127.0.0.1:8906/__pruebas/
uv lock --check
uv run --locked python -m unittest discover -v
uv run --locked python manage.py check
uv run --locked python -m compileall -q actualizador backend frontend tests main.py manage.py desktop.py
git diff --check
```

Las pruebas usan fracciones de referencia obtenidas de los despejes para
comprobar las filas corregidas y una transcripción del script de clase para exigir
iteraciones idénticas bit a bit. También cubren los dos criterios de parada, la falta
de dominancia, la divergencia del ejemplo sin dominancia, el vector inicial exacto, el
límite de iteraciones, diagonal nula, entradas inválidas, desbordamiento, el formato
de los floats (exacto, decimales, ceros falsos, junto a ε y potencias de diez) y la
correspondencia entre tabla, sustitución y motor.

Resultados del rediseño (v0.20.1, 2026-11-23):

- Suite completa de Python: 2122 pruebas correctas; `manage.py check` sin avisos.
- `tests.iterativos_browser`: 8/8 en Edge headless y 8/8 dentro del WebView2 real del
  ejecutable (`build_windows.ps1 -Target App`, Edge 157, ventana 1280 × 698 a 150 %).
- Runners de las piezas compartidas: presentación de resultados 14/14 (`numeros.js`),
  menú de edición 65/65, edición de entradas 350/350 y resultado 111/111.
- Revisión visual en Edge: 1280, 744 y 390 px, claro y oscuro, Estudio y Minimalista,
  sin JavaScript (tabla completa e iteración 1), Exacto y Decimal.

Pendiente: lector de pantalla y táctil físico.

[Familias de Métodos numéricos](capturas/iterativos/00-familias-metodos-numericos.jpg) ·
[Comparación en escritorio](capturas/iterativos/01-clase-escritorio.jpg) ·
[Gauss-Seidel, iteración 2, tema oscuro](capturas/iterativos/02-gauss-seidel-iteracion-2.jpg) ·
[Práctica en móvil](capturas/iterativos/03-practica-movil.jpg) ·
[Formulario en móvil](capturas/iterativos/04-formulario-movil.jpg) ·
[Ejemplos en el menú de edición](capturas/iterativos/05-menu-ejemplos.jpg) ·
[Sin dominancia diagonal](capturas/iterativos/06-sin-dominancia.jpg) ·
[WebView2 real, Exacto](capturas/iterativos/07-webview2-escritorio.jpg)
