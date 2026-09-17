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
