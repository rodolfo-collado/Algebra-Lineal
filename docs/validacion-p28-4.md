# Validación P28.4 — Deshacer último pegado

Base: `origin/develop`, merge de #85
(`0cec894d8f7a8e0f899c1e1b84b9cec1e47d4063`, 10 de octubre de 2026).
Rama: `feature/p28-4-deshacer-pegado`. Sin merge, versión, tag ni release.

## Arquitectura y seguridad

Un solo registro privado en `deshacer_pegado.js`. Recibe los destinos ya
prevalidados por P28.3, consume el registro anterior sin anuncio intermedio y
llama a `entradasSeguras.aplicarPegado`. Conserva únicamente las diferencias
reales del registro `{input, anterior, nuevo}`, sus coordenadas, cuadrícula y
formulario exactos, longitudes de filas, tipo de operando y contexto mínimo de
foco/mensaje. No guarda selección, clipboard, HTML, resultado ni estado visual.
Contrato completo: [Deshacer último pegado](deshacer-pegado.md).

Todo éxito reemplaza el anterior; un éxito sin diferencias lo consume sin crear
acción. Un rechazo conserva el registro previo seguro. Los bloques P27, b separado
de Ax=b, B de Inversa y bloques de Vectores se integran por la misma aplicación;
el pegado nativo en el texto de una sola celda sin selección permanece normal.

Un input/change posterior en la cuadrícula destino invalida undo, incluso en una
celda no afectada. Una edición independiente en otra matriz lo conserva. Un
observador temporal invalida ante retirada/reconstrucción/movimiento DOM y cambios
de editabilidad/visibilidad. Las referencias se liberan al consumir o invalidar;
la comprobación de coordenadas e identidad no permite seguir nombres reutilizados.
`pagehide` descarta el registro incluso si el documento vuelve desde bfcache.

La comprobación final procesa mutaciones pendientes y verifica identidad,
formulario, tipo, dimensiones, existencia, editabilidad y coincidencia literal de
cada valor nuevo esperado. Una celda incoherente implica **cero restauraciones**,
sin rollback parcial. Tras validar todo, consume y restaura con la aplicación
P28.3; emite input por cada diferencia después del bloque completo.

Mensaje persistente y botón real antes de Calcular, separados de presupuesto y
avisos de vectores. La región viva contiene solo el mensaje. La acción desaparece
tras usarse y devuelve el foco a la celda de contexto o un fallback seguro; una
invalidación pasiva no roba foco. Si el botón tenía foco permanece aria-disabled
hasta salir de él. Se conserva la selección actual válida. Stale sigue stale;
Deshacer no calcula, envía ni revalida el resultado.

## Archivos modificados (13)

| Área | Archivos |
| --- | --- |
| Implementación | `frontend/web/calculadora/static/calculadora/deshacer_pegado.js`, `entradas.js`, `styles/modules.css`, `frontend/web/calculadora/templates/calculadora/base.html` |
| Runner y contrato HTTP | `tests/entrada_edicion_browser.js`, `tests/entrada_edicion_browser.py`, `tests/test_entrada_edicion.py` |
| Documentación | `docs/deshacer-pegado.md`, `docs/validacion-p28-4.md`, `docs/pegado-matricial.md`, `docs/seleccion-matricial.md`, `docs/pruebas.md`, `docs/README.md` |

Sin dependencias nuevas ni cambios de backend, algoritmos matemáticos o versión.

## Pruebas

Suite Python completa final: **1641/1641** (82,887 s), después de completar
los enlaces de este documento. Contrato HTTP: 8/8.
Lockfile, Django check, compileall, sintaxis de los JS afectados y
`git diff --check` correctos.

Runner matricial en Browser: **350/350**, conserva los 243 casos anteriores y
añade 107. Las expectativas antiguas de mensajes se actualizan a la cantidad de
celdas realmente cambiadas y a la región exclusiva; eventos P27/P28.3 permanecen.

Incluye un solo uso, reemplazo global A/B y en la misma matriz, rechazo que conserva
undo, no-op que lo consume, orden por filas, rectángulos, siete comandos, Ctrl,
diagonal/triangular/irregular como máscara sobre celda y selección, b aumentado y
separado, Inversa B, P27 y Vectores. Vacíos, fracciones, decimales, valores iguales
y mezcla de diferencias; identidad DOM y tipo, dimensiones, eliminación real,
readonly/disabled/fieldset/hidden/maxlength, movimiento/reconstrucción/retirada y
reinserción, con observer pendiente y entregado. También valor incoherente sin
input, cero restauraciones parciales, selección nueva y limpia, foco del summary,
foco de botón invalidado pasivamente, B en desplegable cerrado y fallback con
celdas/Calcular bloqueados, eventos completos, Escape/flechas/teclado,
Ctrl+Z nativo, stale irreversible, POST/navegación, bfcache y un único anuncio de
éxito al reemplazar el registro.

Los trece runners suman **658/658** casos DOM en Browser.

| Runner anterior en Browser | Resultado |
| --- | --- |
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
| `resultado_browser` | 66/66 |
| `escritorio_browser` | 27/27 |

El QA visual detectó que `.btn` sobrescribía el display del atributo hidden. Se
corrigió con una regla local y se añadió una comprobación del display real al
consumir/invalidar; no basta comprobar la propiedad DOM hidden.

Browser no ofrece emulación forced-colors en esta sesión. Solo para esa dimensión
se usó Edge headless con Playwright del runtime ya instalado: **358/358 en claro y
358/358 en oscuro**, incluyendo ocho casos de colores de sistema/bordes/foco de
P28.1/P28.4. No se añadieron paquetes al proyecto. Es emulación, no alto contraste
físico de Windows. Se inspeccionaron también capturas con el botón enfocado.

Una repetición concurrente con los runners anteriores falló en el primer caso
P27 de dimensión 3×3 (la cuadrícula permaneció 2×2); oscuro pasó completo.
La repetición aislada de toda la suite pasó 358/358 en ambos esquemas, sin errores
de página. El fallo intermitente no se reprodujo en Browser ni en esa repetición.

## QA manual en Browser

Se usaron controles y portapapeles reales, sin ClipboardEvent sintético:

1. Ctrl+V de bloque 2×2 `1,2,3,4` → botón Deshacer: restauró cuatro vacíos y
   devolvió foco a A11; la acción dejó de ser visible.
2. Diagonal 3×3 con `1`: abrir menú, elegir mediante teclado, Ctrl+V desde summary,
   doce Tab hasta Deshacer y Enter. Restauró las tres celdas y mantuvo selección.
3. Ctrl+clic en orden inverso de tres coordenadas de otra página, Ctrl+C y Ctrl+V
   de máscara irregular: pegó `1,6,8` por filas, conservó seis huecos y restauró
   los tres destinos con Deshacer.
4. Paste 2×2 → editar A11 a `8`: acción oculta, valores `8,2,3,4`, foco conservado
   en A11 y aviso de invalidación. No se restauró encima de la edición.
5. Paste A `1,2,3,4` → paste B `5,6,7,8` → Deshacer: B volvió a cuatro vacíos;
   A mantuvo sus valores y no quedó otro undo. Foco en B11.
6. Flujo completo seleccionar → pegar → Tab → Enter con nombre accesible Deshacer,
   retorno de foco y anuncio único; teclado matemático conservado al volver a celda.
7. Viewport 320×650: rango manual 2×2 con `1/2`, cuatro Tab hasta Deshacer,
   claro/oscuro y Enter. Restauró vacíos, foco en A22 y sin desborde horizontal.

El runner verifica las cuatro herramientas a **1280×650, 744×521 y 320×650**,
en claro y oscuro, con foco visible y sin scroll horizontal de página. La prueba
manual móvil usa el iframe de tamaño fijo existente del runner, con app, DOM y
scripts reales; el override de viewport de Browser no cambió las dimensiones de
su página nativa. No se presenta ese intento como validación móvil. Consolas de
las páginas manual y móvil revisadas: sin errores ni advertencias.

Evidencia local fuera del repo, en la carpeta de visualizaciones de esta sesión:
`suite-python.txt`, `suite-python-final.txt`, `regresiones-dom.json`,
`forced-colors.json`, `p28-4-mobile-paste.png`, `p28-4-mobile-dark.png`,
`p28-4-mobile-undo.png` y `p28-4-forced-light.png` / `p28-4-forced-dark.png`.
Los eventos de portapapeles sintéticos se limitan al runner y al harness de QA
forced-colors, nunca al código de producción.

## Límites y entrega

Sin QA físico de WebView2, Excel, Sheets, menú contextual nativo, lector de
pantalla, táctil o alto contraste de Windows. Sin redo, historial ilimitado,
undo de edición normal ni Ctrl+Z global. Undo restaura solo valores: jamás estructura.

Commits Conventional Commits de implementación/pruebas y documentación.
PR hacia `develop`; su estado de CI se informa por separado de estas pruebas
locales. No se hace merge ni se cambia versión, tag o release.
