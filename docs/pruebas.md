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

El incremento de operandos y notación visual amplía estos mismos runners:
`tests.operandos_browser` comprueba nombres iniciales y largos, mayúsculas,
altas, renombrados, cambios de tipo y bajas, selección/cursor/foco, deshacer,
lista vacía y ocultación al abrir Opciones o editar la estructura.
`tests.teclado_browser` comprueba la inserción literal de `ᵀ` y la fuente
de operandos también sobre un `input` compatible. Las suites
`test_traspuesta_expresiones` y `test_expresiones_matriciales_web` conservan
la equivalencia `A^T`/`Aᵀ`; las inversas y potencias siguen fuera del lenguaje.

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
GET previo los IDs live con Python para 40 consultas, incluidas las siete
obligatorias, acciones naturales, tildes, mayúsculas, espacios Unicode y todos
los términos ignorados. Véase [validación P27.5](validacion-p27-5.md).

## P27.6 — Resultado y procedimiento

```bash
uv run --locked python -m tests.resultado_browser
```

Abrir `http://127.0.0.1:8883/__pruebas/` en Browser. El runner sirve POST reales
de Django y scripts/CSS de producción; no necesita Playwright ni dependencias
nuevas. Sus 66 casos comprueban las siete herramientas: conservar el resultado
anterior, una sola transición/anuncio, selección del contenido y nuevo POST
vigente; cambios de método, operación, dimensiones, expresión, casillas,
destinos y estructura; exclusión de tema y presentación; busy, `pageshow` y
foco del POST inválido. Las fixtures comparten la cookie CSRF para permitir la
inspección simultánea en otra pestaña sin invalidar sus formularios.

Mide geometría real en 1280×650, 1084×721, 744×521, 640×325 y 390×650 para
inversas 4×4 con fracciones, 6×6, 8×8 y 10×10, reducción 8×9, matriz
rectangular 2×10, Ax=b y Bases con 39 cifras. Verifica ausencia de overflow de
página, ambos corchetes dentro del scroll, última columna accesible, ausencia
de scroll anidado, wrap y dirección de la flecha, Tab condicionado por overflow
y cambios de viewport/Exacto/Decimal. El procedimiento largo comprueba sticky
por estilo y posición después de bajar 6000 px, y Resultado visible al plegar.
También cubre procedimiento 3×3 sin paradas extra y HTML sin JavaScript.

`test_resultado_presentacion` verifica el contrato declarativo de las siete
herramientas, corchetes/columnas completos y conclusión de verificación real
con ambos métodos y propiedad adicional. Las pruebas de inversa conservan el
conteo de motores/productos y cubren fallo de verificación y matriz singular
sin falso ✓. Se actualizaron las expectativas históricas de `tabindex="0"` y
resultado oculto; no se modificaron las referencias matemáticas.

Validación local P27.6: **1565 pruebas Python**, **66/66** en este runner y las
regresiones DOM: presentación **10/10**, feedback **19/19**, inversa **7/7**,
teclado contextual **30/30**, buscador **16/16**, entradas **19/19** y operandos
**15/15**. `manage.py check`, `compileall`, `uv lock --check` y
`git diff --check` pasan.

QA principal con el plugin oficial Browser sobre localhost, con árbol AX,
DOM, Tab real, scroll nativo e inspección visual en los cinco viewports. Anchos
`scrollWidth/clientWidth` de página observados: **1265/1265**, **1069/1069**,
**729/729**, **625/625** y **375/375**, respectivamente (se excluye la barra
vertical). En Resultado de inversa 8×8 hay una sola región horizontal: ancho
660 px, contenido 2441 px y final alcanzado en `scrollLeft=1781`; última
columna y cierre visibles. Ax=b pequeño recorrió 30 Tab reales sin entrar en
contenedores de matrices. El scroll ancho sí recibe Tab, nombre y foco normal,
y ArrowRight desplaza nativamente. Reducción 8×9 mantuvo el summary en y=56
tras bajar hasta y=8125; al plegar, Resultado quedó en y≈204.

Se capturaron fila Antes/Después, wrap con fracciones, última columna 8×8,
resultado anterior, sticky, verificación, [A | I] 10×10 a 744 px y Bases a
390 px. Las imágenes permanecen fuera del repositorio. No se observaron
pantallas en blanco, overlaps ni errores nuevos de consola/recursos en la
ejecución final. Teclado, Escape, Menú, buscador, Exacto/Decimal y foco de error
mantienen los contratos P27.3–P27.5.

Incidencias de Browser recuperadas: conexión inicial rechazada antes de que el
servidor escuchara; timeout del selector por rol para `summary`, resuelto con
su locator DOM nativo; viewport aplicado a otra pestaña, corregido midiendo
`innerWidth/innerHeight` de la pestaña inspeccionada. Una pestaña antigua de
error de conexión no pudo reutilizarse por la política de URL del Browser;
se continuó en una pestaña válida. Un registro histórico del runner numérico
contenía un TypeError de MutationObserver; la recarga terminó 10/10 sin errores
nuevos y no se reprodujo. No se usó Playwright externo ni fallback. Esta QA
cubre el navegador integrado; no añade validación de otros motores o desktop.

## P27.7 — Experiencia de escritorio

```bash
uv run --locked python -m tests.escritorio_browser
```

Abrir `http://127.0.0.1:8882/__pruebas/`. El runner sirve la app real con
`DEBUG=False`, en modo escritorio o web según la cookie `p277=web`, y un archivo
de preferencias temporal. Sus 25 casos cubren Alt+←/→ sobre GET y sobre un
resultado POST (vuelve desde la caché, con los datos calculados y sin reenvío),
Alt+← desde una celda, Ctrl/Shift/AltGr/IME sin navegar y la web sin
interceptar Alt+flecha ni el menú contextual; `pageshow` restaurado (cajón,
`inert`, foco, tema, Exacto/Decimal y precisión sin stale ni anuncio repetido,
junto a la espera de P27.4); categorías del Menú solo en `sessionStorage`;
preferencias en el archivo propio y su vuelta en un arranque nuevo; y las
páginas 404, 400, 403, CSRF y 500 a 1280, 744 y 390 px sin desborde, con
«Ir al inicio» enfocable. Si la pestaña está oculta, espera con temporizador.

`tests.test_escritorio` prueba el archivo de preferencias (lista blanca,
archivo dañado, escritura atómica, hilos simultáneos), el endpoint (CSRF, 400,
405 y 404 en la web), `data-desktop` solo en escritorio, `autocomplete="off"`,
los contratos de historial; `tests.test_paginas_error`, las páginas de error con
`DEBUG=False`.
`tests.test_desktop` añade ventana maximizada y su geometría al restaurar,
ruta de preferencias fuera de repositorio, instalación y temporales, modo
privado, puerto efímero, dos instancias simultáneas, el filtro del menú nativo
con dobles de .NET y, en el smoke Waitress, el 404 propio y una preferencia
guardada por HTTP. El menú nativo, los atajos y el foco reales solo se validan
en WebView2; véase [validación P27.7](validacion-p27-7.md).

## P27.8 — Pulido visual y accesibilidad

```bash
uv run --locked python -m tests.pulido_browser
```

Abrir `http://127.0.0.1:8885/__pruebas/`. El runner sirve la app y sus scripts
reales; los 16 casos usan formularios y POST de verdad. Comprueban que `-11/13`,
`123/456`, `-123456` y `3.14159` se leen completos en Ax = b, Inversa, Operaciones,
la matriz aumentada y Vectores a 1280, 744, 390 y 760 px, con columnas alineadas y sin
desborde de página; también una matriz 1×1 en el tamaño mínimo desktop y una 10×10
donde más allá de 7rem la celda conserva cursor y scroll local;
Calcular dentro del primer viewport a 1920×1010, dos tarjetas por fila y una sola
columna a 390 px; foco y aviso al agregar y quitar símbolos y vectores (nunca en
body); el × dentro de su fila; nombres por símbolo al renombrar; la ayuda asociada a
cada aplicación de la inversa; un solo desplegable (chevrón al inicio, mismo tamaño,
abre y cierra, grupos sin «▸») con el procedimiento como único sticky; etiquetas
asociadas, sin «:» y con el mismo estilo y separación en las siete herramientas;
contraste calculado de bordes (normal, foco y error) y placeholders en claro y
oscuro; y anclas y foco bajo la cabecera y bajo el summary sticky. Compara medidas
entre sí y relaciones de contraste, no píxeles ni colores escritos. Con la pestaña
oculta cede el turno con `MessageChannel`: no hay `requestAnimationFrame` y los
temporizadores se agrupan.

En Python, `test_procedimiento_plegable` fija el contrato del componente (chevrón
primero, icono, h6 y detalle opcionales) y que ninguna plantilla de herramienta
escribe `<details>`; `test_propiedades_inversa_web`, la ayuda por opción y su
`aria-describedby`, que conserva la descripción del error;
`test_expresiones_matriciales_web`, el grupo y los botones por símbolo, también
renombrado sin JavaScript, y los labels reales sin «:»; y
`test_multiplicacion_matrices_web`, los grupos de producto con el componente. Véase
[validación P27.8](validacion-p27-8.md).

## P27.9 — Entrada y edición de datos

```bash
uv run --locked python -m tests.entrada_edicion_browser
uv run --locked python -m unittest tests.test_entrada_edicion -v
```

Abrir `http://127.0.0.1:8889/__pruebas/` en @Browser. Sus 33 casos sirven formularios
y scripts reales: pegado exacto/interior/fila/columna, LF/CRLF, signos/fracciones/
decimales/espacios, single-cell nativo, comas, atomicidad ante overflow y filas
desiguales, `maxlength` real de vector lineal, readonly/disabled de origen y destino,
solo `text/plain`, input/status/foco/teclado/stale y los cinco módulos. También
defaults 3 ecuaciones × 3 variables, memoria al alternar y redimensionar, POST con
error, primer cambio tras POST textual, fallback textual sin JS y Aplicar de Ax=b.
Las flechas cubren extremos/interior, selección, modificadores, AltGr, IME y
`defaultPrevented`, con paridad entre Reducción y Ax=b; conserva navegación vertical.
Cuatro casos miden fracciones largas, 7rem, alineación y scroll local a 1280×650,
744×521, 390×650 y 760×560.

`test_entrada_edicion` aporta seis pruebas Python sobre el parser existente,
ayuda/placeholder asociados y aceptados, defaults, dimensiones explícitas,
conservación POST/error y cálculo por texto sin JS. Los casos positivos incluyen
x1/x2, fracciones, punto decimal, espacios y separadores `;`, LF y CRLF; los
negativos incluyen X1, x/y/z, coma decimal, `;` final vacío y espacios entre dígitos.

El `ClipboardEvent` simulado se usa únicamente en el runner. La QA adicional en
@Browser prueba Ctrl+C → Ctrl+V reales entre texto tabulado y otra cuadrícula,
selección/cursor reales con `-12/7`, el teclado contextual y los cuatro tamaños.
No sustituye una prueba nativa del menú de WebView2; el handler no depende de Ctrl+V.
Se ejecutan además los diez runners anteriores, 225 casos. Comandos, resultados
y límites: [validación P27.9](validacion-p27-9.md).

## P27.11 — Claridad de entrada y candidato 0.9.0

```bash
uv run --locked python -m tests.claridad_browser
uv run --locked python -m unittest tests.test_claridad_p2711 -v
```

Abrir `http://127.0.0.1:8887/__pruebas/`. Sus 30 casos usan formularios, CSS y
scripts reales: temas de una herramienta abiertos en Inicio y restaurados tras el
filtro; las siete herramientas sin kicker (migas → título → descripción);
«Ecuaciones» y la separación tras Método/Entrada a 1280 y 390 px en ambos modos;
etiqueta y ayuda de Romanos por dirección, también sin JavaScript, y sus errores
orientativos; Base de origen antes del número, perfil del teclado y validación al
cambiarla y conversión de `1A`; vectores `v1…v4` al agregar, quitar, cambiar de
operación y con dimensión 10; ayudas numéricas con decimales; y 390×650 en claro y
oscuro sin desborde.

`test_claridad_p2711` fija los contratos en Python: «Álgebra lineal» desde el
catálogo, `herramienta_unica`, layout sin kicker, título común de relacionadas y
exploraciones, sugerencia de dirección solo cuando la otra conversión es válida,
orden de Bases, ayudas, coma decimal sin conversión (y sin sugerencia para
`1,000` o listas), vectores `v1`…, filtro `incognitas`, Ax = b sin mezcla de `x1`
y `x₁`, «Resultado» y la leyenda de pivotes. `entrada_edicion_browser` suma seis
casos de pegado: líneas vacías exteriores con LF, CRLF y varias, una fila vacía
interior que se sigue rechazando y un valor rodeado de saltos que conserva el
paste nativo. Las capturas congeladas de P26.3 y P26.4 aplican
`tests.ayudas.antes_de_p2711`, que deshace solo el título del panel, la leyenda y
la notación. `test_release` comprueba que la versión preparada coincide con
`uv.lock` y no retrocede de 0.9.0.

Los casos que necesitan foco real (teclado contextual tras `focus()`) requieren una
ventana con foco: con el panel de Browser oculto se ejecutan en Chrome headless con
emulación de foco por CDP, sin dependencias nuevas. Véase
[validación P27.11](validacion-p27-11.md).

## P28.1 — Selección matricial

Se amplía `tests.entrada_edicion_browser`, sin otro servidor ni dependencia:

```bash
uv run --locked python -m tests.entrada_edicion_browser
```

Abrir `http://127.0.0.1:8889/__pruebas/`. Incluye gestos en las cuatro herramientas,
texto dentro del input, navegación P27, Escape del teclado/buscador/cajón,
siete comandos sobre A, matrices rectangulares, A/b, API, dimensiones,
reemplazos, bajas/reindexado, tipos excluidos, B adicional de inversa, resultado
vigente, edición con teclado matemático y POST sin persistencia. Comprueba
menú, foco y desborde a 1280×650, 744×521 y 320×650 en claro y oscuro.

En un navegador con `(forced-colors: active)`, abrir
`/__pruebas/?forced-colors=1` añade cuatro casos que exigen la emulación activa
y comparan bordes/foco con Highlight y CanvasText. No simulan alto contraste
inyectando una paleta en la página. El contrato HTTP está en
`tests.test_entrada_edicion`: plantilla única, siete botones sin nombre/submit,
región viva y alcance de scripts. Ejecutar también la suite completa y los
runners anteriores. API: [selección matricial](seleccion-matricial.md).
Resultados y límites: [validación P28.1](validacion-p28-1.md).
