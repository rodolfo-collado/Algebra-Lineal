# P27.10 — Accesibilidad y responsive residual

7 de octubre de 2026, America/Managua. `git fetch origin develop` confirmó
`aa569a9613c5f240d39342e5b0eac22f2df9abe6`, merge de P27.9 (#78).
Rama: `feature/p27-10-accesibilidad-responsive-residual`; PR hacia `develop`.
Sin merge, versión, tag, release, dependencias ni cambios matemáticos.

## Inspección y reproducción anterior al cambio

Se revisaron P27.8/P27.9, tokens, CSS compartido, header, tema inicial,
tema.js, navigation.js, vectores.js/entradas.js, buscador, numeric_results,
numeros.js, plantillas, documentación y runners. Se aplicó la skill
frontend-testing-debugging disponible, con @Browser como superficie principal.

| Problema | Evidencia en la base |
| --- | --- |
| UI-68.1 | En Chromium forced-colors, las tres líneas de fondo de Menú toman el color del fondo; el botón queda vacío a 390 px. |
| UI-68.2 | Tab real a Reducción: outline de 3 px tanto en el radio como en la pastilla. |
| UI-68.3 | AX expone Tema como toggle/checkbox; al cambiar a oscuro anuncia «Cambiar a tema claro» con estado activado. |
| UI-68.4 | En una página con JS realmente deshabilitado, Tema es visible y no actúa. |
| UI-45 | A 390 px, Tab a u10 desplaza u 452 px y deja v/v3 en cero; cada fila tiene overflow auto. |
| UI-64 | Reducción a 390 px: grupos de 68.84 px de alto con radio de cápsula; selección recortada visualmente. |
| UI-53, solo Formato | A+B con ocho entradas enteras: cero nodos convertibles y Formato visible. |
| UI-20, solo enlaces | Buscar Gauss/Matriz/Vectores carecen de clase compartida y subrayado. |

No se cambiaron copy, ranking, navegación, límites, algoritmos, leyenda de pivotes
ni los incrementos pendientes P27.11/P28, incluido el bug de líneas vacías al pegar.

## Contrato final

- **Menú:** las tres líneas existentes se dibujan mediante `border-top: 2px solid
  currentColor`, incluidos los pseudoelementos. El borde sobrevive a forced-colors
  y conserva la geometría normal. No se usa `forced-color-adjust: none`.
- **Identidad del header:** en forced-colors, `.app-brand` y `.app-mark` usan
  `CanvasText`; el path existente hereda ese color mediante `fill="currentColor"`.
  Chromium aplicaba `LinkText` al nombre por su enlace nativo y conservaba el
  color normal del SVG con `preserve-parent-color`: el tema oscuro producía una
  marca blanca sobre el Canvas claro (y el caso inverso, negra sobre Canvas oscuro).
  No se desactiva la adaptación de colores del sistema ni se impone verde de marca.
  El enlace a Inicio conserva semántica, foco y activación; breadcrumbs y otros
  enlaces siguen usando los colores de enlace del sistema. Los temas normales
  conservan sus colores anteriores.
- **Radios:** `.option` y `.segment` conservan su outline de `:focus-visible`;
  solo el radio interno deja de dibujar un segundo outline. El radio nativo
  mantiene selección, teclado y representación en alto contraste.
- **Tema:** HTML nace con `hidden`; CSS respeta ese atributo y tema.js lo revela
  después de instalar su acción. No tiene `aria-pressed`. AX en claro:
  `button, Cambiar a tema oscuro`; en oscuro: `button, Cambiar a tema claro`,
  sin propiedad pressed. tema_inicial.html y el acceso a preferencias quedan
  intactos: persistencia, tema inicial sin flash, desktop y pageshow conservados.
- **Sin JS:** Tema y el botón del cajón están ausentes; la navegación está
  disponible y los formularios conservan Aplicar y POST. Se comprobó también
  Aplicar para tres vectores de dimensión 10 sin JS.
- **Vectores:** `#vector-list` es el único contenedor con overflow horizontal.
  Filas y componentes usan subgrid para compartir nombres y ancho por columna,
  incluso si una sola celda crece con field-sizing. La dimensión validada existente
  publica el número de columnas en HTML y al redibujar. El × ocupa su columna
  después del paréntesis; se alcanza desplazando la lista o mediante Tab.
  Las filas carecen de scroll independiente y la página no desborda.
- **Segmented:** hasta 480 px, grupo y opciones reutilizan `--radius-md`.
  Se conservan orden, radios, selección, foco y diseño desktop. A 390 px los
  grupos de Reducción, Bases y Romanos se revisaron en ambos temas; Ax=b e Inversa
  también conservan el foco de sus pastillas.
- **Formato:** se revela únicamente si `#resultado` contiene al menos un
  `[data-numeric]`. Esa metadata procede de `numeric_results`/`variantes`:
  existe solo si el texto exacto difiere de su representación decimal en alguna
  precisión soportada (2/4/6/8). Incluye el bloque de resultado y su procedimiento,
  sin una segunda detección por JS. Los atributos accesibles se sincronizan cuando
  hay texto convertible; atributos solos no justifican ofrecer un cambio visual.
  Enteros, texto puro y literales ya idénticos en el contrato actual permanecen
  ocultos. Fracciones y racionales redondeables lo muestran. No se cambia ni borra
  la preferencia global; una herramienta posterior la recupera. No se recalcula.
- **Buscador:** las tres sugerencias reutilizan `text-link`. Mantienen destinos,
  copy y búsqueda, con subrayado y foco inequívocos, también al hacer hover.

## QA renderizada

@Browser: DOM/AX, screenshots, interacción y runners con la aplicación real.
Los cinco tamaños se prueban en iframes de los runners. Chromium/Edge con
Playwright ya instalado complementa con viewports superiores exactos, Tab real,
emulación forced-colors y JS deshabilitado. Sin dependencias nuevas.

| Viewport | Dimensión 10: suma/resta, tres vectores, ambos temas |
| --- | --- |
| 1280×650 | Alineación conservada; sin scroll necesario para los valores probados. |
| 900×650 | Scroll local común; Tab a componente 10 desplaza todas las filas. |
| 760×560 | Scroll local común; columnas y × separados. |
| 480×650 | Scroll local común; Menú reconocible sin texto visible. |
| 390×650 | Scroll local común; última componente y × accesibles sin superposición. |

60 combinaciones: 2 temas × 5 viewports × dimensiones 2/3/10 × suma/resta.
Se probó añadir con Enter, Tab hasta la última componente, Shift+Tab, scroll
manual, Tab al × y eliminar con Space, con foco contextual. Las posiciones
de columna se comparan entre filas, sin imponer coordenadas de 1 px.
Todas las filas mantuvieron scrollLeft cero; únicamente se desplazó la lista.
El ancho de página nunca superó su ancho visible. En @Browser se pegó realmente
un bloque 2×10 con Ctrl+V: 20 valores y status «Se pegaron 20 valores.».

Menú: claro/oscuro, los cinco tamaños, Enter/Space y Escape con retorno de foco.
Tema: AX en ambos estados, Enter/Space, persistencia y pageshow. Radios:
Tab real en Reducción, Ax=b, Inversa, Bases y Romanos, foco único y visible.
Buscador vacío: hover, Tab/Shift+Tab, ambos temas y 390 px.
Formato: A+B entero oculto; Inversa diag(3,2) y Ax=b con b=(1,1) visibles,
recuperando Decimal/6; pageshow y stale tras editar. Fixture adicional con
1234567/10000000 redondeable, entero 4, decimal idéntico 0.5 y texto puro.

Forced-colors **emulado** en Chromium/Edge: Menú y sus tres bordes en ambos
temas y cinco tamaños; foco y estado nativo de radios; segmented; enlaces de
búsqueda. También se emuló prefers-reduced-motion: controles funcionales y
transiciones desactivadas. No se usó Windows High Contrast físico.
Sin página vacía, overlay de error ni errores de consola en la QA específica.

Corrección del header en la misma rama y PR #79: QA normal claro/oscuro en
@Browser y Edge, y forced-colors claro/oscuro emulado en Edge, a 390×650,
760×650 y 1280×650. Se capturaron y revisaron los cuatro estados; también se
cruzaron ambos temas de aplicación con ambos esquemas forced-colors: 18
combinaciones en total. Logo y nombre visibles, Menú/Tema visibles y sin
overflow de página. Tab real y Shift+Tab conservan el foco de los tres controles;
Enter en la identidad vuelve a Inicio, Space activa Menú/Tema y Escape retorna
al botón Menú. AX conserva `link, PyGebra, inicio`. El runner residual compara
los colores efectivos con sondas `CanvasText`/`LinkText`, sin exigir RGB concretos;
pasó 39/39 tanto en el esquema forced-colors claro como en el oscuro.

## Validación automática y regresiones

| Comando | Resultado |
| --- | --- |
| uv run --locked python --version | Python 3.13.3 |
| uv run --locked python -m unittest discover -v | 1621 OK, 82.005 s (repetición del header) |
| uv run --locked python manage.py check | Sin problemas, 0 silenciados |
| uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py | OK |
| uv lock --check | OK, 30 paquetes |
| git diff --check | OK |
| node --check | tema.js, numeros.js, vectores.js y runners modificados, OK |

| Runner en @Browser | Resultado |
| --- | --- |
| residual_browser (P27.10) | 39/39, también en forced-colors claro/oscuro |
| presentacion_browser | 14/14 |
| entrada_edicion_browser (P27.9) | 33/33 |
| pulido_browser (P27.8) | 16/16 |
| resultado_browser (P27.6) | 66/66 |
| escritorio_browser (P27.7) | 27/27 |
| teclado_browser (P27.3) | 30/30 |
| feedback_browser (P27.4) | 19/19 |
| buscador_browser (P27.5) | 16/16 |
| entradas_browser | 19/19 |
| operandos_browser | 15/15 |
| inversa_browser | 7/7 |

Los contratos desktop de aria-pressed se actualizaron a su ausencia, conservando
los nombres y la comprobación de pageshow. Al ejecutar varios runners a la vez
en el mismo origen hubo interferencia de cookies CSRF; resultado pasó 66/66
en repetición y escritorio pasó 27/27 de forma aislada. Se usa un origen fresco para evitar caché de estáticos de QA previa
y se separan las ejecuciones que escriben cookies o preferencias.
Para la corrección del header se repitieron además pulido (16/16), escritorio
(27/27) y buscador (16/16), junto a todos los comandos de validación anteriores
y la sintaxis JS del runner residual. Los demás runners registran la QA inicial.

## Límites y seguimiento

- AX y emulación no sustituyen un lector de pantalla físico ni WebView2 nativo.
  No se realizó instalación Windows manual. El CI, incluida Distribución de
  Windows, se verifica aparte en la PR; esta tabla registra pruebas locales.
- La detección de Formato conserva el alcance del adaptador existente: variantes
  preparadas para literales racionales, sin ampliar el parser a textos nuevos.
- Capturas, logs y script CDP complementario quedan fuera del repositorio.
  Solo se versionan contratos y runners necesarios; no se añade infraestructura.
