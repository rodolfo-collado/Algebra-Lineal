# Validación P28.5 — Copiar matrices de resultado

Base: `origin/develop`, merge #86, `ce4683f951530e3183f640077d8eaf314d0a50ab`.
Rama: `feature/p28-5-copiar-resultados`. Destino: `develop`.
Fecha: 10 de octubre de 2026, America/Managua.

## Inspección y alcance

- Operaciones muestra una matriz final para expresiones matriciales, una matriz
  determinada y hasta dos valores matriciales en una igualdad. Vectores y escalares
  que usan esa herramienta conservan su presentación y no reciben acciones.
- Reducción mostraba la matriz escalonada/reducida en Procedimiento cuando estaba
  activado. P28.5 mueve ese bloque al panel final, una vez por método, con pivotes
  y nombre de método al comparar. Antes/Después, sistema resultante y sustitución
  siguen siendo explicativos; no reciben botones.
- Inversa muestra A⁻¹ o una matriz final de la propiedad seleccionada: inversa de
  inversa, traspuesta o producto. La aplicación a b muestra un vector y queda fuera.
  A, [A|I], inversas intermedias e identidades/productos de verificación pertenecen
  a Procedimiento, sin Copiar.
- Ax=b muestra x como vector, solución parametrizada o contradicción; equivalencias,
  aumentadas y comprobación son explicativas. No se amplía a vectores. Vectores,
  bases y romanos carecen de resultados matriciales dentro del alcance.

Contrato de uso: [copiado matricial](copiado-matricial.md#matrices-del-resultado-final-p285).

## Arquitectura y exactitud

`matriz.html` publica `data-valor-exacto` solamente al recibir `copiar` en un
resultado final. Usa el literal que ya entrega el backend a la celda, escapado por
Django. Los helpers `formatear_matriz`/`formatear_exacto` conservan racionales;
`numeric_results` prepara variantes y `numeros.js` cambia solo la presentación.
Las copias no leen decimales redondeados ni reconstruyen fracciones.

La extracción mínima de `serializarValores` deja `serializar` como adaptador de
inputs P28.2. Botones y selección comparten generación TSV/HTML/metadata y la
escritura del evento copy. El botón usa la acción de usuario y
`document.execCommand("copy")`, conservando el tipo propio sin prefijo `web `.
No hay otro script de portapapeles, dependencias, API de paste o versión MIME.

Salida: `text/plain` TAB/LF exacto; `text/html` tabla mínima con fracciones como
`=1/3` y el escape/tratamiento Excel ya elegido en P28.2; tipo propio v1 con
`forma: rectangulo`, todas las coordenadas relativas desde cero y dimensiones
reales. Se serializan todas las celdas del DOM, incluidas las desplazadas.
Límites intactos: 12 filas, 13 columnas, 120 posiciones, TSV 64 KiB y metadata 4 KiB.

El estado stale conserva Copiar y su aviso de entrada anterior. La acción no
recalcula, emite input/change, modifica entradas, selecciona resultados ni toca
undo P28.4. Cada matriz tiene un botón nativo con nombre contextual y su propia
región viva discreta, separada del feedback de pegado/deshacer. Sin JavaScript
solo se oculta la acción, manteniendo todo el contenido matemático.

## Archivos

| Área | Archivos |
| --- | --- |
| Núcleo y estilo | `static/calculadora/copiar_matricial.js`, `styles/modules.css` |
| Componentes | `components/matriz.html`, `matrix.html` |
| Resultados | `modules/expresiones/index.html`, `_lado.html`, `_determinacion.html`; `modules/inversa/index.html`; `modules/sistemas/index.html`, `_matriz_final.html`, `_bloques_metodo.html`, `_pivotes.html` |
| DOM/HTTP | `tests/entrada_edicion_browser.js`, `resultado_browser.js`, `resultado_browser.py`, `test_resultado_presentacion.py` |
| Contratos previos | `tests/ayudas.py`, `test_procedimiento_plegable.py`, `test_interfaz_progresiva.py`, `test_resolver_sistema.py`, `test_reduccion_filas.py`, `test_regresion_sistemas_bloques.py`, `test_matriz_inversa_web.py`, `test_claridad_p2711.py` |
| Documentación | `docs/copiado-matricial.md`, `interfaz.md`, `pruebas.md`, `README.md`, este informe |

Las rutas de frontend de la tabla están bajo `frontend/web/calculadora/`.
No se modifican algoritmos, forms, selección, pegado o undo.

## Pruebas y QA

Suite completa: `uv run --locked python -m unittest discover -v`,
**1645/1645 correctas**, 204,524 s. Las primeras ejecuciones detectaron expectativas
antiguas de ubicación y texto; se actualizaron para el contrato P28.5 conservando
las fixtures matemáticas congeladas. Los 167 tests afectados también pasaron en
la comprobación dirigida.

Los trece runners DOM en Browser completaron **705/705 casos**, sin fallos:

| Runner | Casos correctos |
| --- | ---: |
| `entrada_edicion_browser` (P28.1–P28.4) | 350/350 |
| `resultado_browser` (incluye P28.5) | 113/113 |
| `operandos_browser` | 23/23 |
| `entradas_browser` | 19/19 |
| `inversa_browser` | 7/7 |
| `feedback_browser` | 19/19 |
| `buscador_browser` | 16/16 |
| `pulido_browser` | 16/16 |
| `residual_browser` | 39/39 |
| `claridad_browser` | 30/30 |
| `teclado_browser` | 32/32 |
| `presentacion_browser` | 14/14 |
| `escritorio_browser` | 27/27 |

Pasaron además `uv lock --check`, `manage.py check`, compileall de backend/frontend/
tests, `node --check` del núcleo y los dos runners modificados, y `git diff --check`.
El runner de resultados no registró errores ni avisos de consola.

Browser es la superficie principal de interacción y runners. Se calculó una
inversa diagonal con 1/3, cero y −1/2 mediante el formulario real; Copiar anunció
éxito, conservó foco y resultado vigente. En el iframe de QA de 320×650 se calculó
la misma inversa, se recorrió Resultado → Formato → Procedimiento → Copiar con Tab
y se activó con Enter y Space, también en Decimal y tema oscuro: sin overflow,
foco conservado y feedback único. El DOM mantenía `1/3` al mostrar `0.3333`.
El tamaño usa el iframe fijo existente, no un dispositivo físico.
Su portapapeles virtual no recoge la
escritura iniciada por execCommand desde botón: `clipboard.read()` retornó vacío
y Ctrl+V fue rechazado por el transporte virtual. Recuperar una pestaña válida
resolvió el intento inicial de conexión anterior al arranque del servidor.

Para la dimensión de portapapeles se utilizó Edge headless con Playwright del
runtime instalado, sin paquetes nuevos. Siete recorridos con controles y teclado
reales, sin ClipboardEvent sintético, pasaron:

1. Calcular → Tab desde Resultado hasta Copiar → Enter → textarea: TSV 2×2 exacto,
   tres MIME, HTML `=1/3` y metadata completa.
2. Exacto → Decimal → Space → textarea; vuelta a Exacto: los tres formatos idénticos.
3. Copiar → Ctrl+V en Operaciones: P28.3 recibió y pegó el bloque exacto.
4. Pegar sobre A → resultado stale → Copiar → Deshacer: acción conservada y
   valores originales restaurados; no hubo cálculo automático.
5. Resultado rectangular Decimal con 1/3, negativos, cero y enteros → textarea →
   entrada 2×3 con Ctrl+V, sin rutas especiales.
6. Tab/Space y feedback con viewport real 1280×650, 744×521 y 320×650,
   sin scroll horizontal de página; captura visual del botón enfocado.
7. Consolas sin errores de página en esos recorridos.

Es QA automatizado de navegador real, no QA físico de Windows. Evidencias locales
fuera del repo: `clipboard-edge.cjs`, `clipboard-edge.json`,
`p28-5-1280.png`, `p28-5-744.png`, `p28-5-320.png`, logs de suite y contratos,
en la carpeta de visualizaciones de esta sesión.

## Límites y entrega

Sin QA nuevo de Excel, Sheets, WebView2, lector de pantalla físico, táctil físico
o menú contextual nativo. El HTML conserva el tratamiento de P28.2 ya validado;
las hojas externas mantienen sus límites de precisión. Si el motor no admite
execCommand/copy o falla un límite/escritura, se comunica el fallo sin éxito parcial.
No hay selección parcial ni acciones en Procedimiento.

Commits Conventional Commits y PR hacia develop; CI se registra separadamente
de las pruebas locales. Sin merge, cambio de versión, tag ni release.
