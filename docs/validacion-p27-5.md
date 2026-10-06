# P27.5 — Buscador y orientación

Base: `origin/develop` en `aec68d8`, merge de P27.4 (#73).
Rama: `feature/p27-5-buscador-orientacion`.
Validación: 5 de octubre de 2026, America/Managua.

## Alcance y resultado

| Incidencia | Comportamiento |
| --- | --- |
| UI-15 | Inicio y cualquier `/?q=` conservan una sola fila por herramienta del catálogo completo, incluidas próximas. Sin JS, el GET muestra solo coincidencias y oculta el resto. Live reutiliza esas filas sin otro GET; al limpiar restaura temas/apertura o permite explorar todas desde un GET previo. |
| UI-16 | Normalización NFD, eliminación de marcas, minúsculas, separación compartida e ignorado de términos genéricos. Las acciones útiles están en el catálogo; no se añaden frases completas para parchear cada consulta. Una consulta sin términos significativos devuelve cero coincidencias. |
| UI-17 | Álgebra Lineal y Matrices explicitan sistemas. Reducción parte del sistema escrito/matriz aumentada; Ax = b de A y b conocidos. Sistemas devuelve Reducción y Ax = b, en ese orden. Relacionadas muestra nombre e invitación; Operaciones con matrices añade inversa. |
| UI-20 | Límites aparece en live con Próximamente y Cálculo tiene badge en Menú. Vacíos ofrecen enlaces reales. Escape lateral limpia antes de cerrar; GET con búsqueda enfoca resultados con contorno de 3 px. Live no roba foco ni duplica el estado inicial servidor. |

No se implementan UI-18/UI-19. No hay cambios de `pageshow`, bfcache, tema,
escritorio, historial, teclado, formularios, algoritmos, rutas, versión ni dependencias.
No se hace merge, tag ni release.

## Semántica GET/live

`catalogo.py` sigue siendo la única fuente de verdad. `datos_buscador()` publica
con `json_script` el índice y nombre normalizados, estado, orden del registro,
palabras vacías y expresión de separación. El cliente no declara herramientas.
La expresión de espacios es explícita porque Python y JS difieren en `\s`.
Python elimina marcas Unicode con `category`; JS usa `\p{M}` tras NFD.

Ambos exigen que cada término significativo aparezca como subcadena del índice.
El orden es: disponibles antes de próximas, más aciertos en el nombre y orden
del registro. El runner compara los IDs del JS real con Python para **38
consultas desde dos estados iniciales**: Inicio y `/?q=gauss` (76 comparaciones).
Incluye la tabla obligatoria y palabras vacías, tildes, mayúsculas y espacios
Unicode. La lista y el separador se verifican también contra el JSON renderizado.

Lista exacta ignorada, después de normalizar: `de`, `a`, `al`, `el`, `la`, `los`,
`las`, `un`, `una`, `calcular`, `hallar`, `metodo`, `pasar`.
`método` se normaliza a `metodo`. Solo esos 13 términos se ignoran.

En un GET no vacío, primero se renderizan las coincidencias en orden y luego las
demás filas con `hidden`. El status live nace vacío. Al editar se oculta el bloque
servidor completo; volver al texto exacto restaura sus filas, encabezado y recuento.
Un GET vacío de resultados no tiene heading/recuento huérfano. Sus sugerencias
son Buscar Gauss, Buscar Matriz y Buscar Vectores, con URLs construidas mediante
`{% url 'calculadora:inicio' %}?q=`. Con JS se sitúan dentro de la región enfocada.

En Inicio sin consulta las áreas próximas permanecen ocultas. Live mueve las
mismas filas a una lista para respetar el orden global y al limpiar las devuelve
a sus temas. El lateral mantiene el árbol: abre grupos con coincidencias y
restaura su apertura previa sin guardar las aperturas temporales del filtro.

## Consultas naturales

El destino indicado es el primer resultado; operaciones con matrices también
puede coincidir con operaciones de vectores que admite.

| Consulta | Primer resultado |
| --- | --- |
| calcular inversa | Matriz inversa |
| invertir matriz | Matriz inversa |
| multiplicar matrices | Operaciones con matrices |
| sumar vectores | Operaciones con vectores |
| restar vectores | Operaciones con vectores |
| convertir a binario | Conversión de bases |
| pasar decimal a binario | Conversión de bases |
| método de gauss | Reducción por filas |
| reducir matriz | Reducción por filas |
| transponer / trasponer | Operaciones con matrices |
| sistema de ecuaciones / sistemas de ecuaciones | Reducción por filas, seguida de Resolver Ax = b |
| sistema lineal / sistemas lineales / ecuaciones lineales | Reducción por filas, seguida de Resolver Ax = b |
| límites | Límites de funciones, Próximamente |

Se comprueban mayúsculas y espacios repetidos; `MÉTODO de GAUSS` y `LÍMITES`
encuentran las mismas herramientas que sus formas sin tildes.

## Copy y orientación

- Álgebra Lineal: «Vectores, matrices, sistemas de ecuaciones y sus aplicaciones.»
- Matrices: «Operaciones con matrices, sistemas de ecuaciones, reducción por filas, la ecuación matricial Ax = b y la matriz inversa.»
- Reducción por filas: «Resuelve sistemas de ecuaciones con Gauss o Gauss-Jordan, desde el sistema escrito o una matriz aumentada.»
- Resolver Ax = b: «Si ya tienes A y b, encuentra x en Ax = b mediante reducción por filas.»

Las invitaciones finales y las relaciones disponibles son:

| Herramienta | Invitación cuando es destino | Relacionadas, en orden |
| --- | --- | --- |
| Reducción por filas | Parte de un sistema escrito o una matriz aumentada y sigue la reducción. | Resolver Ax = b |
| Resolver Ax = b | Si ya tienes A y b, encuentra x en Ax = b. | Reducción por filas; Operaciones con matrices; Operaciones con vectores |
| Operaciones con matrices | Combina operaciones con matrices, vectores y escalares. | Resolver Ax = b; Operaciones con vectores; Matriz inversa |
| Operaciones con vectores | Suma o resta vectores y encuentra coeficientes de una combinación lineal. | Resolver Ax = b; Operaciones con matrices |
| Matriz inversa | Si necesitas invertir una matriz cuadrada, sigue el procedimiento. | Operaciones con matrices; Resolver Ax = b |
| Conversión de bases | Cambia un número entre binario, octal, decimal y hexadecimal. | Conversión de números romanos |
| Conversión de números romanos | Convierte entre números arábigos y romanos. | Conversión de bases |
| Límites de funciones | Sin invitación, próxima y sin relaciones | Ninguna |

Relacionadas conserva su condición previa: después de un resultado y cuando no
hay exploraciones contextuales. Reducción conserva su conexión educativa a Ax = b;
Ax = b muestra la invitación de Reducción y Operaciones muestra Ax = b e inversa.
Las pruebas verifican el componente completo y POST reales de estas dos páginas.
Ax = b no relaciona Matriz inversa ni propone resolver sistemas por inversión.

## Validación

| Comando | Resultado |
| --- | --- |
| `uv run --locked python -m unittest discover -v` | 1562 pruebas, OK, 67.234 s |
| `uv run --locked python -m unittest tests.test_navegacion tests.test_interfaz_progresiva -v` | 58 pruebas, OK |
| `uv run --locked python -m unittest tests.test_navegacion tests.test_expresiones_matriciales_web tests.test_matriz_inversa_web tests.test_ecuaciones_matriciales_web -q` | 149 pruebas, OK |
| `uv run --locked python manage.py check` | Sin problemas, 0 silenciados |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK |
| `uv lock --check` | OK; 30 paquetes, sin cambios del lock |
| `git diff --check` | OK |
| `node --check` en buscador, navegación y runner nuevo | OK |

Las expectativas antiguas cambiadas corresponden a contratos intencionales:
el DOM completo contiene las próximas ocultas, sistemas incluye Ax = b,
vacíos contienen URLs reales y Operaciones añade inversa entre sus relacionadas.
Se conservaron las expectativas de copy que siguen siendo compatibles.

| Runner DOM | Resultado |
| --- | --- |
| `uv run --locked python -m tests.buscador_browser` — 8881 | 16/16; 76 comparaciones Python/JS |
| `uv run --locked python -m tests.entradas_browser` — 8878 | 19/19 |
| `uv run --locked python -m tests.operandos_browser` — 8877 | 15/15 |
| `uv run --locked python -m tests.inversa_browser` — 8879 | 7/7 |
| `uv run --locked python -m tests.teclado_browser` — 8766 | 30/30 |
| `uv run --locked python -m tests.presentacion_browser` — 8876 | 10/10 |
| `uv run --locked python -m tests.feedback_browser` — 8880 | 19/19 |

Total DOM: **116/116**, sin errores JavaScript. El runner nuevo añade regresión
para un GET inicialmente sin coincidencias que se edita y vuelve al estado vacío.

## QA renderizada

Skill: `frontend-testing-debugging`. Browser plugin no disponible; se usa
Playwright 1.62.1 y Edge 154.0.4258.53 ya instalados. No se instalan dependencias.
Entorno: `http://127.0.0.1:8881/`. Capturas/scripts auxiliares fuera del repositorio.

| Comprobación | 1280×650 | 744×521 | 390×650 |
| --- | --- | --- | --- |
| Identidad, contenido significativo y ausencia de overlay de error | PASS | PASS | PASS |
| A: Inicio → calcular inversa → GET → enlace Matriz inversa | PASS | PASS | PASS |
| B: `/?q=gauss` → editar inversa sin submit | PASS | PASS | PASS |
| C: sistema de ecuaciones → Reducción seguida de Ax = b, copy distinto | PASS | PASS | PASS |
| D: Menú → límites → área/categoría abiertas y Próximamente visible | PASS | PASS | PASS |
| E: Escape con texto limpia y mantiene abierto; vacío cierra | PASS | PASS | PASS |
| Foco GET visible de 3 px; GET normal/live conservan foco | PASS | PASS | PASS |
| Estado anterior oculto y restaurable; sugerencias ejecutan GET | PASS | PASS | PASS |
| Sin scroll horizontal nuevo | PASS | PASS | PASS |
| Consola: errores o warnings de aplicación | Ninguno | Ninguno | Ninguno |

Se comprueba además sin JS que gauss, inversa, límites y zzz muestran exactamente
sus coincidencias. Las capturas de sistemas muestran las descripciones distintas;
las del Menú móvil muestran Cálculo y Límites con sus badges de Próximamente.
Un POST real de operaciones verifica y captura las invitaciones de Ax = b,
vectores e inversa en los tres tamaños, sin desbordamiento horizontal.

## Riesgos restantes

- Se validó Edge; Firefox/Safari y otros viewports quedan sin QA renderizada.
- Roles, foco, ocultación y anuncios se verificaron en DOM; no se usó un lector de pantalla real.
- El matching sigue siendo por subcadenas, sin stemming ni sinónimos inferidos. Las acciones soportadas se declaran en el catálogo.
- UI-19 (tema al volver, drawer en bfcache y navegación `pageshow`) permanece fuera de alcance.

## Archivos modificados

Lista exacta del incremento, incluidos los nuevos:

- `docs/arquitectura.md`
- `docs/interfaz.md`
- `docs/pruebas.md`
- `docs/validacion-p27-5.md`
- `frontend/web/calculadora/catalogo.py`
- `frontend/web/calculadora/context_processors.py`
- `frontend/web/calculadora/static/calculadora/buscador.js`
- `frontend/web/calculadora/static/calculadora/navigation.js`
- `frontend/web/calculadora/static/calculadora/styles/components.css`
- `frontend/web/calculadora/templates/calculadora/base.html`
- `frontend/web/calculadora/templates/calculadora/components/related_tools.html`
- `frontend/web/calculadora/templates/calculadora/components/search.html`
- `frontend/web/calculadora/templates/calculadora/components/sidebar.html`
- `frontend/web/calculadora/templates/calculadora/pages/_area.html`
- `frontend/web/calculadora/templates/calculadora/pages/inicio.html`
- `frontend/web/calculadora/views.py`
- `tests/buscador_browser.js`
- `tests/buscador_browser.py`
- `tests/test_expresiones_matriciales_web.py`
- `tests/test_interfaz_progresiva.py`
- `tests/test_navegacion.py`
