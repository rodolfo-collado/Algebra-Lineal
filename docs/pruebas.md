# Pruebas y verificaciones

[Índice de documentación](README.md) · [Portada](../README.md)

Desde la raíz del repositorio:

```bash
uv lock --check
uv sync --locked
uv run python -m unittest discover -v
uv run python manage.py check
```

Las de `tests/` cubren las reglas matemáticas del backend (validaciones, matrices
rectangulares, pivotes, escalonamiento, sustitución regresiva y clasificación de
sistemas), las expresiones lineales y su formato, la traducción de una matriz a
su sistema, el conjunto solución con variables libres, el parser de sistemas, la
equivalencia entre Gauss y Gauss-Jordan, el flujo de la terminal, la interfaz web
de Django —incluidas sus entradas textual y matricial—, la infraestructura
desktop, el registro de herramientas, la navegación, el buscador, los
breadcrumbs, el teclado matemático, las opciones de Resolver un sistema
—método, comparación, bloques del resultado y rutas antiguas—, la conversión de
bases —resultados, pasos del procedimiento, mensajes de error, conversiones a
varias bases con el decimal calculado una sola vez y su integración web—, las
operaciones con vectores —suma, resta, escalar, combinación lineal
con solución única, infinitas o inconsistente, dimensión arbitraria, fracciones
exactas, la reutilización del motor de sistemas, la estructura dinámica del
formulario y los POST manipulados—, las operaciones con matrices —suma, resta,
escalar y traspuesta en rectangulares, fracciones exactas, procedimiento por
entrada, catálogo, selector, estructura dinámica, errores asociados a celdas
y POST manipulados—, los productos `AB` y `Ax` —producto punto, dimensiones
compatibles e incompatibles, rectangulares, fracciones, equivalencia exacta
entre fila por columna y por columnas (también contra la combinación lineal de
`backend/vectores.py`), tercera dimensión, vector x, selector de método,
comparación con un solo resultado y POST manipulados—, la ecuación matricial
`Ax = b` —matriz aumentada `[A | b]`, casos cuadrados y rectangulares con
solución única, infinitas o inconsistente, fracciones, equivalencia exacta con
Resolver un sistema y entre Gauss y Gauss-Jordan, comprobación `A · x = b`,
interpretación como combinación lineal, b derivado de las filas y x de las
columnas, flujo Aplicar sin JavaScript y POST manipulados— y que la interfaz
no cargue fuentes ni scripts remotos.
Sirven para detectar regresiones cuando el proyecto crezca.

Para el teclado contextual P17, `uv run python -m unittest tests.test_teclado -v`
comprueba perfiles válidos, inserciones compatibles con el parser, un componente
por herramienta, contextos de campos, datos de bases compartidos, ocultación
sin JavaScript y nombres de controles POST. Los helpers distinguen los
formularios de cálculo del buscador y excluyen los controles inertes de `template`.
Las suites web de cada herramienta conservan sus pruebas de POST y resultados.

Para el procedimiento plegable P18, `uv run python -m unittest
tests.test_procedimiento_plegable -v` comprueba con un parser HTML
estructural que en Sistemas, Vectores, Matrices y Ax = b hay un único «Ver
procedimiento» (`details` nativo, cerrado, con su título como encabezado)
antes del único panel de resultado, que queda fuera de él; que el
procedimiento conserva los pasos, equivalencias, desarrollos y métodos; que la
clasificación, la solución, los coeficientes y la matriz obtenida aparecen una
sola vez; que el ancla `#resultado` y la jerarquía de encabezados se
mantienen; que sin JavaScript todo el contenido está en el HTML; y que Inicio
y Conversión de bases no cambian. Las suites de cada herramienta se adaptaron
al orden Entrada → Procedimiento plegable → Resultado.

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
la publicación. La validación del tag puede comprobarse localmente y en pruebas
sin crear tags en este repositorio; consulta [Releases](releases.md).
