# P27.9 — Entrada y edición de datos

Base sincronizada con `git fetch origin develop`: `40fbc59bf239d52010fab8f0e207a257106d2bfe`,
merge de P27.8 (#77). Rama: `feature/p27-9-entrada-edicion-datos`. Destino: `develop`.
Validación: 7 de octubre de 2026, America/Managua.

## Alcance e inspección

UI-26, UI-28, UI-30 y UI-38. Sin UI-74, transferencia automática, nuevos parsers,
dependencias, algoritmos, desktop/build, versión, tag, release ni merge.

| Superficie | Flujo inspeccionado | Decisión |
| --- | --- | --- |
| Reducción | SistemaForm → json_script → matriz.js → input[data-cell] | Reutilizar memoria por coeficiente/b; default 3 ecuaciones × 3 variables. |
| Ax=b/Inversa | FormularioCeldas → matriz_entrada/celda → ecuaciones.js/inversa.js | El paste usa filas de cada tabla; A y b/B conservan grids independientes. |
| Operaciones | forms_expresiones → símbolos/tablas → expresiones.js | Misma adaptación de tabla, incluidos símbolos nuevos y vectores lineales. |
| Vectores | VectoresForm → _fila → vectores.js | Filas visibles por vector, columnas por componente; excluir k. |
| Compartidos | entradas.js, teclado.js, resultado.js, P27.8 CSS y runners existentes | Un listener paste y una guarda de flechas en entradas.js; reutilizar input/stale/perfiles y CSS. |

No se introduce un motor de spreadsheet ni otra política de resultados.

## Contrato final del paste

- Solo `text/plain`; TAB para columnas, LF/CRLF para filas. Una terminación de
  línea no crea una fila adicional. Trim en extremos; no se eliminan signos,
  fracciones ni espacios internos. Sin columnas por comas.
- Si queda un único valor y no hay TAB, se deja paste al navegador.
- Se inspecciona todo el bloque antes de escribir: rectangularidad, espacio,
  celdas editables y maxlength. No hay paste parcial ni cambio de dimensiones.
- Ejemplo de error: «El bloque no cabe en la cuadrícula. Lo pegado ocupa 3×4 y
  desde esta celda solo caben 2×3. No se pegó ningún valor.»
- Readonly/disabled de origen conservan el comportamiento nativo; si aparecen
  entre los destinos se rechaza el bloque entero. Tampoco se escribe en resultados,
  previews, procedimiento ni x simbólico.
- `maxlength` del DOM es la fuente del límite textual por celda. El límite
  existente de componentes lineales (200) se publica desde Python y se conserva
  al reconstruir. Las celdas numéricas no tenían maxlength: no se inventa uno ni
  se duplica el límite de dígitos del parser. El runner verifica su rechazo al
  calcular, igual que una entrada escrita.
- Primero se asignan todos los valores; después se emite input por destino.
  Los observadores ven el bloque completo, sin submit ni cálculo automático.
- Foco inicial conservado; status de Operaciones/Vectores reutilizado y región
  status propia en los otros formularios. «Se pegaron 9 valores.» Sin alert().
- El resultado anterior permanece visible y recibe el estado desactualizado de
  resultado.js. Su mensaje y el teclado contextual conservan sus contratos.
- En Vectores la orientación corresponde a lo mostrado: TAB recorre componentes;
  una columna LF recorre vectores. En Ax=b/Inversa el vector b se muestra vertical.
- Los enlaces de exploración quedan intactos; el usuario copia y elige el destino.

## Dimensiones y edición

Reducción propone **3 ecuaciones × 3 variables**, una matriz aumentada visual 3×4.
Ax=b conserva su default 2×2: no hay razón para imponerlo a Reducción. SistemaForm
publica el default; el JS solo completa dimensiones ausentes en la primera visita
tras un POST textual. No sustituye datos de un POST matricial ni ediciones posteriores.
Alternar texto → matriz conserva 5×4 y valores, incluido b al cambiar variables.
Sin JS se conserva el cálculo textual de Reducción y Aplicar en los otros módulos.

←/→ editan dentro del input. Solo navegan sin selección, al inicio/al final
respectivamente. La guarda compartida ignora Ctrl, Alt, Shift, Meta, AltGr, IME
incluido keyCode 229 y defaultPrevented; evita destinos readonly/disabled.
↑/↓ conservan la navegación de filas. El runner compara Reducción y Ax=b.

## Forma libre: contrato verificado

| Entrada | Parser web real |
| --- | --- |
| x1, x2 | Aceptadas; x2 solo conserva la columna x1 con coeficiente cero. |
| X1, x, y, z | Rechazadas. |
| 1/2x1 = -11/13 | Aceptada exactamente con Fraction. |
| 3.14x1 = -2 | Aceptada; punto decimal. |
| 3,14x1 = 2 | Rechazada; coma decimal. |
| Ecuaciones separadas por ;, LF o CRLF | Aceptadas. |
| ; final vacío | Rechazado. |
| Espacios entre términos y en 1 / 2 | Aceptados. |
| Espacios entre dígitos: 1 2x1 | Rechazados por la protección existente. |

Ayuda final, asociada al textarea y compatible con sus errores:

> Usa x1, x2, … como incógnitas, con x minúscula. Puedes escribir enteros,
> fracciones como 1/2 y decimales con punto. Separa las ecuaciones con ; o con
> saltos de línea. Ejemplo: 2x1 - x2 = 3; x1 + 4x2 = 7. No uses x/y/z, X1,
> coma decimal ni un ; vacío al final. Puedes dejar términos a ambos lados del =,
> como x1 - 6 = -x2.

Placeholder válido conservado y probado literalmente, sin ; final:

```text
x1+2x2-x3=4;
2x1-x2+3x3=7;
x1+x2+x3=6
```

## Pruebas y regresiones

| Verificación | Resultado |
| --- | --- |
| uv run --locked python --version | Python 3.13.3 |
| uv run --locked python -m unittest discover -v | 1621 pruebas OK, 99.245 s |
| uv run --locked python manage.py check | Sin problemas, 0 silenciados |
| uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py | OK |
| uv lock --check | OK, 30 paquetes |
| git diff --check | OK |
| node --check | Seis scripts de producción modificados y runner P27.9, OK |

| Runner en @Browser | Resultado |
| --- | --- |
| entrada_edicion_browser | 33/33 |
| entradas_browser | 19/19 |
| operandos_browser | 15/15 |
| inversa_browser | 7/7 |
| teclado_browser | 30/30 |
| feedback_browser | 19/19 |
| buscador_browser | 16/16 |
| presentacion_browser | 10/10 |
| resultado_browser | 66/66 |
| escritorio_browser | 27/27 |
| pulido_browser | 16/16 |
| Total | 258/258 |

P27.1 conserva memoria, dimensiones inválidas y límites; P27.3, teclado contextual;
P27.4, errores, foco, busy y submitter; P27.6, stale y resultado/procedimiento;
P27.7, Alt+flechas y contratos de edición/privacidad; P27.8, field-sizing, grids,
foco dinámico y scroll local. Se ajustan tres tests Python que exigían la ubicación
anterior de las guardas, ausencia de defaults o copy anterior; el comportamiento
nuevo se prueba con eventos DOM y parser/POST reales.

## QA principal en @Browser

Sin fallback a Playwright externo. Identidad de páginas, contenido significativo,
ausencia de overlays, DOM/AX, screenshots e interacción comprobados.

- Texto tabulado en textarea de Reducción → selección → Ctrl+C real → Inversa
  3×3 → Ctrl+V real: nueve valores, foco A11, status y teclado visibles.
- Ctrl+V real en aumentada: 12 valores con -11/13, 3.14 y -2; otra prueba pega
  27 fracciones largas en 3 filas × 9 columnas. No se calcula automáticamente.
- Flechas reales con -12/7 en Reducción y Ax=b: cursor 3 → ← posición 2 →
  → posición 3; selección 12 [1,3], Shift+← y Ctrl+← permanecen en la celda.
  Los extremos navegan a columna anterior/siguiente. El runner prueba los demás
  modificadores, selección, defaultPrevented y composición.
- Claro a 1280 px y oscuro a 390 px: grid, fracciones, foco y teclado observados.

Medidas del documento tras paste real largo, viewport efectivo confirmado:

| Viewport | Página scrollWidth/clientWidth | Scroll local matriz | Máximo input |
| --- | --- | --- | --- |
| 1280×650 | 1265/1265 | 1166/1134 | 112 px, 7rem |
| 744×521 | 729/729 | 1166/631 | 112 px, 7rem |
| 390×650 | 375/375 | 1166/285 | 112 px, 7rem |
| 760×560 | 745/745 | 1166/647 | 112 px, 7rem |

Sin desborde horizontal de página. La primera medición del runner miraba el
wrapper externo: se corrigió para medir `.matrix-grid-frame`, el scroll local real.
El viewport se aplicó inicialmente a otra pestaña; se repitió sobre una nueva
pestaña QA y se verificó innerWidth/innerHeight antes de registrar estas medidas.

Consola de P27.9/páginas normales sin errores. Escritorio encontró un SecurityError
en iframe al probar historial mientras otros runners navegaban; una pestaña nueva,
ejecutada aisladamente, terminó 27/27 sin errores. Presentación numérica registró
un MutationObserver sobre un nodo inválido: tras recargar terminó 10/10 sin un
registro nuevo. Es el mismo tipo de incidencia documentada en P27.8; no se modificó
su código ni se reprodujo en las páginas normales de P27.9.

## Archivos y entrega

Implementación y pruebas: commit `bcf6af9`. Documentación en commit independiente.

```text
docs/interfaz.md
docs/pruebas.md
docs/validacion-p27-9.md
frontend/web/calculadora/forms.py
frontend/web/calculadora/forms_expresiones.py
frontend/web/calculadora/static/calculadora/ecuaciones.js
frontend/web/calculadora/static/calculadora/entradas.js
frontend/web/calculadora/static/calculadora/expresiones.js
frontend/web/calculadora/static/calculadora/inversa.js
frontend/web/calculadora/static/calculadora/matriz.js
frontend/web/calculadora/static/calculadora/vectores.js
frontend/web/calculadora/templates/calculadora/modules/expresiones/index.html
frontend/web/calculadora/templates/calculadora/modules/sistemas/index.html
tests/entrada_edicion_browser.js
tests/entrada_edicion_browser.py
tests/test_entrada_edicion.py
tests/test_escritorio.py
tests/test_interfaz_progresiva.py
tests/test_resolver_sistema.py
```

## Límites

No se ejecutó build/instalación Windows local ni interacción del menú contextual
nativo de WebView2. Ctrl+V real y el evento paste están probados; el contrato usa
el mismo evento para el menú nativo, sin detectar la combinación de teclas.
No se validaron otros motores ni lectores de pantalla físicos. Sin undo manager:
el paste de una celda conserva el navegador, sin garantía de undo atómico para bloques.
Las capturas se mostraron en la conversación y los logs permanecen fuera del repo.
