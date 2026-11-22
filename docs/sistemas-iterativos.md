# Jacobi y Gauss-Seidel en Ax = b

Abre **Métodos numéricos → Sistemas lineales → Métodos iterativos** e ingresa
la matriz cuadrada A y el vector b. Puedes elegir **Jacobi**, **Gauss-Seidel** o
**Comparar ambos**. La comparación parte del mismo vector inicial para los dos
métodos. Si dejas el vector inicial vacío, PyGebra usa ceros.

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

## Ejemplos de clase y correcciones

Los ejemplos se cargan desde el formulario. El de clase aparece en el Word
`Ejemplos_Paso_a_Paso_Jacobi_Gauss_Seidel.docx` y la diapositiva 9 de
`Presentacion_Jacobi_Gauss_Seidel.pptx`. La solución exacta es `(1, 2, −1, 1)`.
Con los valores predeterminados se obtienen 15 iteraciones por Jacobi
(`‖r‖∞ ≈ 4.663227e−5`) y 6 por Gauss-Seidel (`‖r‖∞ ≈ 7.697313e−5`).

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
uv run --locked python -m unittest tests.test_sistemas_iterativos tests.test_sistemas_iterativos_web -v
uv lock --check
uv run --locked python -m unittest discover -v
uv run --locked python manage.py check
uv run --locked python -m compileall -q actualizador backend frontend tests main.py manage.py desktop.py
git diff --check
```

Las pruebas usan fracciones de referencia obtenidas de los despejes para
comprobar las filas corregidas. También cubren los dos criterios de parada,
la falta de dominancia y de convergencia, diagonal nula, entradas inválidas,
desbordamiento y la correspondencia entre la tabla, los operandos y el resultado.

- Pruebas focalizadas. 178 correctas sobre el motor, la ruta nueva, la
  navegación, la búsqueda, los formularios y los métodos directos.
  La comprobación adicional del catálogo de Estudio y la ruta dio 37 correctas.
  El archivo del motor y sus pruebas matemáticas coinciden byte por byte con
  los de la revisión anterior del PR.
- Suite completa de Python. 2.068 pruebas correctas. También pasaron la
  verificación del lockfile, Django, compilación, sintaxis de JavaScript y
  `git diff --check`.
- Runners de navegador del proyecto. Buscador 21/21, edición de entradas
  350/350 y presentación de resultados 111/111.
- Edge 158 con Playwright. Escritorio a 1366 px y móvil a 390 px en ambos
  temas, además de colores forzados. Se comprobaron las tres familias,
  el enlace desde Ax = b, el selector, el foco, la tabla y las sustituciones.
  Sin JavaScript se comprobó el enlace del área, **Aplicar** para cambiar
  dimensiones, el cálculo y la primera sustitución. Se ejercitó también la
  gráfica con residuos muy pequeños a 320 px.
- axe-core 4.14.1. Sin hallazgos en las reglas automatizadas de WCAG A/AA
  ejecutadas en los cinco perfiles de navegador. La prueba móvil se hizo
  por emulación. Quedan pendientes el lector de pantalla y el paquete
  instalado de Windows/WebView2.

[Familias de Métodos numéricos](capturas/iterativos/00-familias-metodos-numericos.jpg) ·
[Resultado en escritorio](capturas/iterativos/01-clase-escritorio.jpg) ·
[Gauss-Seidel, iteración 2 y gráfica](capturas/iterativos/02-gauss-seidel-iteracion-2.jpg) ·
[Resultado de práctica en móvil](capturas/iterativos/03-practica-movil.jpg) ·
[Formulario en móvil](capturas/iterativos/04-formulario-movil.jpg)
