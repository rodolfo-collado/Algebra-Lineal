# Pruebas y verificaciones

[Índice de documentación](README.md) · [Portada](../README.md)

Desde la raíz del repositorio:

```bash
uv lock --check
uv sync --locked
uv run python -m unittest discover -v
uv run python manage.py check
```

Operandos múltiples: `uv run python -m unittest tests.test_operandos_multiples`
cubre aridad, colecciones exactas, dimensiones consecutivas, cadenas de tres y
cuatro matrices como expresiones (`A + B + C`, `ABCD`), ambas lecturas del
producto, validación estricta del POST y el presupuesto común de P26.6: hasta 50
símbolos, 900 celdas y 990 campos de estructura y celdas, comprobados antes de
construir el formulario y dentro del límite de campos por envío de Django, y en
la expresión hasta 50 operandos, 49 operaciones y 900 entradas contando cada
aparición (también cadenas de traspuestas y signos). Vectores conserva sus
pruebas de 50 vectores.

Para comprobar los controles en un DOM real, ejecuta
`uv run python -m tests.operandos_browser` y abre
`http://127.0.0.1:8877/__pruebas/`. Los quince casos usan la aplicación Django y
los scripts de producción. En vectores: añadir/quitar, eliminar uno intermedio,
mínimos por operación y el tope de 50. En Operaciones con matrices: agregar y
eliminar símbolos conservando nombres y valores, una resta real de tres
agrupada por la izquierda, nombres después de Z (A1, B1…), el tope de 50
símbolos, el presupuesto de celdas que detiene Agregar, dimensiones, steppers y
cambios de tipo que no caben y no cambian nada, flechas dentro de la cuadrícula,
una cantidad manipulada y `ABCD` con las tres lecturas del producto.
Este ejecutor local no añade dependencias ni se lanza en `unittest discover`.

Entradas seguras (P27.1): `uv run --locked python -m tests.entradas_browser`
en `http://127.0.0.1:8878/__pruebas/` comprueba los scripts de producción en
formularios Django reales. Cubre recuperación de celdas al reducir y aumentar
dimensiones, memoria por tipo de símbolo, vectores y escalar, independencia
de la columna b, dimensiones inválidas sin reemplazar nodos, presupuestos,
feedback y `aria-invalid`, mínimos/máximos de los steppers, Enter hacia la
acción principal y el fallback sin JavaScript. La rueda se verifica sin
cancelar su evento; conviene comprobar también con una rueda física que la
página sigue desplazándose. `tests.test_entradas_seguras` valida Aplicar sin
JavaScript y `tests.test_seguridad_numerica` rechaza espacios numéricos antes
de convertirlos, conservando `1 / 2`, `- 3` y los saltos entre ecuaciones.

Las de `tests/` cubren las reglas matemáticas del backend (validaciones, matrices
rectangulares, pivotes, escalonamiento, sustitución regresiva y clasificación de
sistemas), las expresiones lineales y su formato, la traducción de una matriz a
su sistema, el conjunto solución con variables libres, el parser de sistemas, la
equivalencia entre Gauss y Gauss-Jordan, el flujo de la terminal, la interfaz web
de Django —incluidas sus entradas textual y matricial—, la infraestructura
desktop, el registro de herramientas, la navegación, el buscador, los
breadcrumbs, el teclado matemático, las opciones de Reducción por filas
—método, comparación, bloques del resultado y rutas antiguas—, la conversión de
bases —resultados, pasos del procedimiento, mensajes de error, conversiones a
varias bases con el decimal calculado una sola vez y su integración web—, la
numeración romana —ambos sentidos, canonicidad e integración web—, las
operaciones con vectores —suma, resta, escalar, combinación lineal
con solución única, infinitas o inconsistente, dimensión arbitraria, fracciones
exactas, la reutilización del motor de sistemas, la estructura dinámica del
formulario y los POST manipulados—, las operaciones con matrices —suma, resta,
escalar y traspuesta en rectangulares escritas como expresiones, fracciones
exactas, procedimiento por entrada, catálogo, estructura dinámica, errores
asociados a celdas y POST manipulados—, los productos `AB` y `Ax` —producto punto, dimensiones
compatibles e incompatibles, rectangulares, fracciones, equivalencia exacta
entre fila por columna y por columnas (también contra la combinación lineal de
`backend/vectores.py`), vector x con otro nombre, opción de presentación,
comparación con un solo resultado y POST manipulados—, la ecuación matricial
`Ax = b` —matriz aumentada `[A | b]`, casos cuadrados y rectangulares con
solución única, infinitas o inconsistente, fracciones, equivalencia exacta con
Reducción por filas y entre Gauss y Gauss-Jordan, comprobación `A · x = b`,
interpretación como combinación lineal, b derivado de las filas y x de las
columnas, flujo Aplicar sin JavaScript y POST manipulados—, las expresiones
de Operaciones con matrices —lexer, parser, árbol, traspuesta, tipos, dimensiones, procedimiento por nodo,
subexpresión, fracciones exactas, igualdades verdaderas y falsas, lados no
comparables, rutas `izq`/`der`, regresión contra las primitivas, integración
web, POST manipulado y formato Exacto/Decimal—, las formas lineales
simbólicas —suma, resta, producto por escalar, normalización, coeficientes,
matriz desconocida, `Ax = b` rectangular y fraccionario, variable ajena,
término constante, no linealidad y la regresión numérica de P20 y P21— y que la interfaz
no cargue fuentes ni scripts remotos.
Sirven para detectar regresiones cuando el proyecto crezca.

Para el teclado contextual P17, `uv run python -m unittest tests.test_teclado -v`
comprueba perfiles válidos, inserciones compatibles con el parser, un componente
por herramienta, contextos de campos, datos de bases compartidos, ocultación
sin JavaScript y nombres de controles POST. Los helpers distinguen los
formularios de cálculo del buscador y excluyen los controles inertes de `template`.
Las suites web de cada herramienta conservan sus pruebas de POST y resultados.

Para las ecuaciones en forma libre (P25.2), `uv run python -m unittest
tests.test_parser_sistemas tests.test_expresiones tests.test_presupuesto_sistemas
tests.test_resolver_sistema -v` comprueba que las formas equivalentes de una
ecuación dan la misma representación; constantes y variables en ambos lados,
variables repetidas, términos desordenados, signos, coeficientes implícitos,
fracciones, decimales, espacios, ceros y variables ausentes; el rechazo de lo
no lineal y de la sintaxis inválida con su motivo; que `normalizar_igualdad`
funciona sin la sintaxis de sistemas; que los literales de ambos lados y los
valores agrupados respetan el presupuesto antes de `Fraction` o de construir
filas; la separación por `;`, `\n` y `\r\n` con líneas vacías y ecuaciones
que siguen en la línea siguiente; y, en la web, el bloque «Forma estándar» del
procedimiento, una ecuación por línea tal como la envía el navegador,
Exacto/Decimal y los errores en el campo del sistema.

Para el procedimiento plegable (P18 y P25.1), `uv run python -m unittest
tests.test_procedimiento_plegable -v` comprueba con un parser HTML
estructural que en todas las herramientas con resultado hay un único «Ver
procedimiento» (`details` nativo, cerrado, con su título como encabezado)
antes del único panel de resultado, que queda fuera de él; que el
procedimiento conserva los pasos, equivalencias, desarrollos y métodos; que la
clasificación, la solución, los coeficientes y la matriz obtenida aparecen una
sola vez; que el ancla `#resultado` y la jerarquía de encabezados se
mantienen; que sin JavaScript todo el contenido está en el HTML; que ninguna
herramienta muestra «Entender este resultado»; y que Inicio no cambia. Las
suites de cada herramienta comprueban el orden Entrada → Procedimiento
plegable → Resultado.

Para P19, `uv run python -m unittest tests.test_microinteracciones -v` comprueba
tokens breves, propiedades de transición explícitas, ausencia de retardos y bucles,
cancelación con movimiento reducido (también `::details-content`), pulsación solo
en controles habilitados, foco, selección sin cambios de métricas y entrada de
contenido visible por defecto. Son contratos CSS, no pruebas de percepción visual.
Se complementan con las suites existentes:

- `test_teclado` y runner DOM: perfiles, inserción, foco y campos regenerados.
- `test_procedimiento_plegable`, `test_interfaz_progresiva` y suites web:
  details/summary nativos, resultado único, formularios/POST sin JS, Inicio y Bases.
- `test_navegacion`: navegación; `test_desktop`, `test_instalador`, `test_webview2`
  y `test_recursos_interfaz`: aplicación, recursos empaquetados y `templatetags`.

Revisión manual P19: 1280×720 y 390×844, claro/oscuro, las cinco herramientas;
pulsación, Tab/flechas, opciones y teclado; abrir/cerrar rápidamente procedimientos,
métodos, comprobación, interpretación, opciones e Inicio por temas. Comprobar el
drawer con toggle, Cerrar, backdrop y Escape y verificar restauración del foco.
Repetir con `prefers-reduced-motion: reduce` emulado y sin JavaScript: contenido y
estados deben seguir disponibles. Probar matrices grandes, dimensión máxima de
vectores y cambios repetidos de estructura/operación sin pérdida de valores
compartidos ni colas. El cierre de disclosures y controles `hidden` es inmediato.
No hay JS nuevo ni dependencias para movimiento; no se animan las celdas.

La regresión de JavaScript usa el DOM real del navegador, sin dependencias nuevas:

```bash
uv run python -m tests.teclado_browser
```

Abre `http://127.0.0.1:8766/` en una ventana visible con foco real: los 18 casos
deben indicar `PASS`. En P19 se confirmó 18/18 en el navegador integrado visible;
los fallos anteriores de foco no se reprodujeron en esas condiciones. Se sirven el
componente Django y el motor reales, con un documento aislado por caso. Cubre
cursor, selección, foco, `input` con propagación, retroceso, etiquetas accesibles,
cambios de perfil, campos agregados/eliminados y objetivos no editables; incluye
un perfil de prueba ajeno a las herramientas para comprobar la extensibilidad.
Este ejecutor es local y manual; `unittest discover` y CI no lanzan un navegador.

Completa con la revisión de las cinco herramientas: Sistemas texto ↔ matriz,
dimensiones y operaciones que regeneran campos, bases 2 → 8 → 10 → 16 y uno,
varios o todos los destinos. Comprueba teclado físico, temas claro/oscuro,
escritorio/móvil y ausencia de desbordamiento horizontal de la página. Las
cuadrículas anchas conservan su scroll local. No guardes capturas en el repositorio.

Para comprobar que todo el código compila:

```bash
uv run python -m compileall -q backend frontend tests main.py manage.py desktop.py
```

Antes de abrir un PR, ejecuta también `git diff --check`.
CI ejecuta la suite en Ubuntu y Windows. En Windows construye el instalador y
ejecuta el [smoke real](instalacion-windows.md#comprobar-la-distribución-real)
en una cuenta limpia. El artifact de CI sirve para revisión; no es una release.

Las pruebas de distribución comprueban las directivas de Inno Setup y los
contratos de CI/CD. Las pruebas de documentación revisan archivos y anchors
relativos del README, CONTRIBUTING y docs sin acceder a Internet.
Para un cambio de packaging, las pruebas estáticas no sustituyen el build y
la instalación real; para un cambio visual, tampoco sustituyen la revisión de UI.

El workflow de release reutiliza CI: una prueba, build o smoke fallidos bloquean
la creación del tag y la publicación. La validación del candidato puede comprobarse
localmente y en pruebas sin crear tags en este repositorio; consulta [Releases](releases.md).

## Rediseño PyGebra y presentación numérica

`uv run python -m unittest tests.test_presentacion_numerica -v` cubre valores
exactos, periódicos, negativos, cero, fracciones impropias, acarreo, empates de
redondeo, recorte de ceros, precisión, enteros grandes y detección de aproximación.
También verifica el error máximo de redondeo sobre miles de racionales,
el formato exacto previo, expresiones con índices, HTML escapado y atributos.

Las integraciones prueban Sistemas (ambos métodos y comparación), operaciones
y combinación lineal de Vectores, Matrices, AB, Ax y Ax=b (única e infinitas):
ambas representaciones preparadas, exacto visible sin JS, procedimientos
conservados, controles únicos y ausencia del selector en entradas, errores y
Conversión de bases. `tests.test_identidad_visual` comprueba que el header
deriva del SVG oficial mediante `scripts/sync_brand_mark.py`, y
`tests.test_recursos_interfaz` que `numeros.js` sigue siendo un recurso local.

El comportamiento en el DOM real (cambio de formato, precisiones, vuelta al
exacto, preferencias guardadas o inválidas, sin `localStorage`, migración del
tema histórico y funcionamiento sin JavaScript) se comprueba con el mismo
patrón que el teclado, sin dependencias nuevas:

```bash
uv run python -m tests.presentacion_browser
```

Abre `http://127.0.0.1:8876/`: los 10 casos deben indicar `PASS`. Sirve el
componente, el bloque `numeric_results` y los scripts de producción con un
documento aislado por caso; el fixture ya trae valores exactos preparados por
Django. Es un ejecutor local y manual; `unittest discover` y CI no lo lanzan.

La revisión de navegador debe incluir cambio de formato después del cálculo,
precisiones, volver al exacto, navegación entre módulos, ambos temas, drawer,
Escape/foco, búsqueda y scroll local de matrices en 375 px, tablet, 1100×760
y escritorio amplio. Los controles numéricos no realizan peticiones de cálculo.

## Presupuesto de entrada de Sistemas

`uv run python -m unittest tests.test_presupuesto_sistemas -v` comprueba el
rechazo antes de reservar estructuras por GET/POST, el máximo real de campos
con CSRF, ambos motores y la protección mínima del texto. Consulta
[presupuesto, auditoría y mediciones](presupuesto-sistemas.md).

En `/matrices/reduccion/`, verifica manualmente: una matriz 2×2; escribir dimensiones
100000×100000 conservando las seis celdas; rechazar 11 ecuaciones y 10 variables
(121 celdas); aceptar 12 y 9 (120); botones +/− en los límites; recuperación
tras corregir dimensiones; GET manipulado sin cuadrícula; resolver y comparar,
plegar procedimiento y alternar Exacto/Decimal.

## Presupuesto computacional

`uv run python -m unittest tests.test_presupuesto_computacional -v` comprueba
que una operación pequeña estima menos que una mayor; que Gauss-Jordan y el
producto crecen con cada dimensión; que racionales más complejos aumentan el
factor, más en la aritmética que en el texto mostrado; que combinar
estimaciones suma pasos, cálculo y procedimiento y conserva las partes; que
cálculo y procedimiento se estiman por separado; que estimar no ejecuta ningún
motor ni convierte números a texto (dimensiones de 10⁹ y enteros de casi un
millón de cifras); que la cota acota los pasos reales de Gauss y Gauss-Jordan;
que las categorías crecen con el tamaño y el tiempo es un intervalo
recalibrable; que los límites estructurales no cambian; y que los servicios de
Reducción por filas y Ax = b estiman con el mismo presupuesto de entrada, sin
resolver y sin rechazar nada por su costo. Ninguna prueba mide segundos.

El benchmark es manual: no se lanza en `unittest discover` ni en CI.

```bash
uv run python -m scripts.benchmark_presupuesto
uv run python -m scripts.benchmark_presupuesto --web
```

Consulta el modelo, las opciones y los resultados locales en
[Presupuesto computacional](presupuesto-computacional.md#benchmark).

## Regresiones de Sistemas y bloques aumentados

```bash
uv run python -m unittest tests.test_matrices_bloques tests.test_gauss_jordan_bloques tests.test_presupuesto_bloques tests.test_matrices_aumentadas_web -v
```

Estas pruebas cubren las primitivas exactas, reducción de `[A | B]` y `[A | I]`,
singularidad según pivotes, protección numérica, presupuesto y separación de
bloques en todos los pasos del procedimiento.

`uv run python -m unittest tests.test_regresion_sistemas_bloques -v` compara
Sistemas con fixtures estáticas obtenidas del árbol Git original de `develop`
tras el PR #60 (`79c04d999775387092771538fc3e668c8da47e2a`). Las expectativas
almacenan una sola vez las partes comunes y el prefijo de pasos de los motores;
las pruebas no ejecutan Git ni reproducen el algoritmo de eliminación.

Los siete casos cubren solución única, infinitas, inconsistencia, una matriz
rectangular, fracciones, intercambio de filas y una columna sin pivote. Se
compara el resultado completo del backend (matrices, pivotes, clasificación,
solución y sustitución), todos los pasos antes/operación/después, el parser y
los servicios de entrada textual y aumentada. También se verifica `Ax = b`,
la opción Comparar ambos y el texto completo del panel final de Django para
ambas entradas. La preparación de `[A | I]` y su contrato se describen en
[Matrices aumentadas por bloques](matrices-aumentadas.md).

## Matriz inversa

```bash
uv run python -m unittest tests.test_matriz_inversa tests.test_matriz_inversa_web -v
```

`test_matriz_inversa` cubre Gauss-Jordan sobre `[A | I]` y la regla 2×2 con los
ejemplos del profesor (2×2, 3×3 con intercambio de filas, singular y 1×1),
que ambos métodos coincidan en enteros, negativos, fracciones, intercambios y
400 matrices 2×2 aleatorias, `A · A⁻¹ = I` como comprobación de las pruebas,
la validación (no cuadrada, vacía, valores no exactos y método 2×2 fuera de
2×2), que se reutilice el motor con `columnas_pivote=n`, que la regla 2×2 no lo
use, que la cota del presupuesto acote los pasos reales y el error controlado
ante números demasiado grandes.

`test_matriz_inversa_web` cubre catálogo, Inicio, menú, migas y buscador; el
GET con Gauss-Jordan predeterminado y sin fórmulas en los controles; el radio
2×2 activo solo en 2×2; Aplicar; los POST válidos y manipulados (método 2×2 en
otra dimensión, métodos inválidos, celdas de más o de menos, campos repetidos,
HTML y CSRF); el separador en todas las matrices del procedimiento; el
procedimiento antes del único resultado; Exacto / Decimal; y la confirmación.
Para esta última se fuerzan la categoría y el intervalo con `patch`, sin
matrices enormes ni segundos reales: el aviso no calcula ni parece un error;
Continuar calcula con la firma de la misma entrada; Cancelar redibuja; una
firma de otra matriz o inventada vuelve a preguntar; y la regla 2×2 nunca
pregunta.

En el navegador, verifica manualmente la 2×2 del profesor por ambos métodos,
la 3×3, una singular, una 10×10 de enteros (que hoy pide confirmación: prueba
Cancelar y Continuar), 375 px y escritorio, y ambos temas.

## Numeración romana

`uv run python -m unittest tests.test_numeros_romanos tests.test_numeros_romanos_web -v`
cubre ambos sentidos con los casos de referencia (1, 3, 4, 9, 14, 40, 44, 58,
90, 400, 944, 1963, 2026 y 3999), la ida y vuelta exhaustiva de 1 a 3999 y que,
de todas las cadenas de hasta cuatro símbolos, solo se acepten las canónicas.
También comprueba las minúsculas, los rechazos (0, negativos, 4000, fracciones,
IIII, VV, IC, IL, VX, IIV, XM, MMMM, IVIV, símbolos ajenos, espacios internos y
longitud) antes de volver a convertir y el procedimiento de 1963 ↔ MCMLXIII.
En la web: ruta, catálogo, Inicio, búsqueda, breadcrumbs, cajón, un único
resultado con «Ver procedimiento» plegado, límites, contrato HTTP estricto
(campos ajenos o repetidos y dirección manipulada) y contenido escapado, sin
traceback ni HTTP 500. La página dice Arábigo → romano y Romano → arábigo, y
una regresión impide que vuelva a mostrar «Decimal → romano» o
«Romano → decimal»; «decimal» no se prohíbe en general porque sigue siendo
correcto en Exacto/Decimal y en Conversión de bases.

En `/romanos/conversion/`, verifica manualmente 1963 ↔ MCMLXIII en ambas
direcciones, una entrada en minúsculas, un error de canonicidad (`IIII`), el
procedimiento plegado y abierto, 390 px y escritorio, y ambos temas.

## Reorganización de Reducción por filas (P26.5)

`tests/test_reduccion_filas.py` verifica la ubicación en Matrices, ausencia de
la categoría pública Sistemas de ecuaciones, orden del catálogo, Inicio, menú,
breadcrumbs, formulario canónico y todas las búsquedas nuevas e históricas.
Comprueba las cinco rutas antiguas, consultas con casillas repetidas, entrada
textual/matricial, método sugerido y explícito, POST raíz 200/slugs 308 con cuerpo intacto,
errores de validación y CSRF. El resto de contratos web se ejecuta ahora sobre
`/matrices/reduccion/`, conservando toda su cobertura.

La referencia `tests/fixtures/reduccion_filas_p264.json` se capturó **antes de
editar** desde `develop` en `1e69d3305f3c2ec519e9aac0a61407e6e780ef61` (P26.4).
Guarda los resultados completos de Gauss/Gauss-Jordan y la normalización por
ecuaciones. Las 60 combinaciones (10 casos × 3 métodos × 2 entradas) deben
coincidir exactamente en matrices iniciales/finales, operaciones, sustitución,
clasificación, pivotes, solución general, libres y contradicciones. «Comparar
ambos» coteja ambos resultados contra esa referencia. Los hashes SHA-256 del
texto completo de `section#resultado` capturado verifican también la salida
matemática presentada; no se regeneran con el código bajo prueba.

Casos: solución única, infinitas, inconsistencia, variable libre rectangular,
intercambio de filas, fracciones, términos a ambos lados, variables a la derecha,
ecuación despejada y matriz rectangular sobredeterminada.

Para QA en navegador: comparar `x1+x2=6; x1-x2=2` con `[1,1,6; 1,-1,2]` en los
tres métodos; probar `x1-6=-x2`, dependencia y contradicción. Revisar claro/oscuro,
escritorio/móvil, teclado, Exacto/Decimal, procedimiento plegable, resultado final,
buscador y marcadores antiguos. La entrada textual mantiene el flujo sin JS.
El smoke de Windows exige el enlace canónico; no se renombran recursos ni se
modifica la configuración de empaquetado.

## Operaciones con matrices unificada (P26.6)

`tests/test_traspuesta_expresiones.py` cubre la traspuesta en el motor: `Aᵀ` y
`A^T` como el mismo token y el mismo nodo, precedencia postfija (`ABᵀ` es `A(Bᵀ)`,
`(AB)ᵀ` traspone el producto), segmentación de nombres (`AT`, `M1ᵀ`, ambigüedad),
rechazo de `A^2` y `A^-1` sin interpretarlos, rutas estables (las expresiones sin
traspuesta conservan las suyas), subexpresiones dentro y debajo de una
traspuesta, identidades (`(AB)ᵀ = BᵀAᵀ`), tipos que no se trasponen (vectores,
escalares, simbólicos) y la lista de expresiones del brief (`A+B` … `A(B+C)-2D`)
con su asociatividad, contra las primitivas y sin reordenar productos.

La referencia `tests/fixtures/operaciones_matrices_p265.json` se capturó **antes
de editar** desde `develop` en `c5d241e7df2fb061a6f4eee34346c64b220d78a3`
(P26.5): la salida completa del servicio anterior de Operaciones con matrices
para 40 casos —suma y resta de 2, 3 y 4 matrices, fracciones, el orden de la
resta, escalar entero, fraccionario y negativo, traspuesta cuadrada,
rectangular, 1×n y n×1, `AB`, `ABC`, `ABCD`, rectangulares y `Ax` con las tres
lecturas—. `tests/test_operaciones_matrices_unificadas.py` escribe cada POST
antiguo como símbolos y expresión y exige el mismo resultado en los 40 casos;
en los pasos de suma, resta, escalar y traspuesta, el mismo desarrollo, las
mismas fórmulas, ayudas, factor y traslados; en `AB`, `ABC`, `ABCD` y `Ax`, cada
lectura idéntica (títulos, fórmulas, cada igualdad, columnas, ensamble y grupos)
y los mismos resultados intermedios. Tres o más sumas, que antes se escribían en
una celda (`1 + 4 + 7`), se comparan entrada a entrada con los pasos del árbol.
El mismo archivo prueba la ruta histórica (GET 301 con la consulta, POST 308
con el mismo cuerpo y el mismo resultado, CSRF), el catálogo final, las
búsquedas históricas, el procedimiento por nodos (`A(B + C)`, `(A + B)ᵀ`,
`AB + C`) y las subexpresiones con traspuesta.

Las suites anteriores de Operaciones con matrices (`test_matrices_web`,
`test_multiplicacion_matrices_web`, `test_operandos_multiples`) y de Expresiones
(`test_expresiones_matriciales_web`, `test_expresiones_lineales_web`) se ejecutan
contra `/matrices/operaciones/`. El smoke de Windows envía las operaciones como
expresiones y comprueba la ruta histórica; su bloque HTTP se puede ejecutar
contra un `runserver` local antes del CI.

Para QA en navegador: `A+B`, `A+B+C`, `A-B-C`, `2A`, `AB`, `ABC`, `Ax`,
`A(B+C)`, `AB+C`, `Aᵀ`, `A^T`, `(A+B)ᵀ`, `ABᵀ` y `(AB)ᵀ`; los productos con las
tres lecturas; una matriz rectangular, un vector, un escalar y una igualdad;
Exacto/Decimal en los valores intermedios, procedimiento plegable, resultado
único, «Calcular solo esta parte», móvil y escritorio, claro y oscuro, teclado
matemático, navegación, buscador y `/matrices/expresiones/`.

## P27.5 — Buscador y orientación

`test_navegacion` cubre normalización, términos vacíos, consultas naturales,
orden de sistemas, próximas, universo completo oculto sin JS y renderizado de
invitaciones. Los cambios de expectativas responden a UI-15 y UI-17: Cálculo
oculto existe en Inicio, sistemas devuelve también Ax = b y operaciones
relaciona Matriz inversa.

```bash
uv run --locked python -m tests.buscador_browser
```

Abrir `http://127.0.0.1:8881/__pruebas/`. El runner usa Django y el JavaScript
de producción. Verifica cambios sucesivos sin GET, estados/recuentos, foco,
sugerencias, próximas, Escape y memoria del Menú. Compara desde Inicio y un
GET previo los IDs live con Python para 38 consultas, incluidas las siete
obligatorias, acciones naturales, tildes, mayúsculas, espacios Unicode y todos
los términos ignorados. Véase [validación P27.5](validacion-p27-5.md).
