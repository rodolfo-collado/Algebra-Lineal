# P27.8 — Pulido visual y accesibilidad

Base verificada tras `git fetch origin develop`: `c9ead90`, merge de P27.7 (#76).
Rama: `feature/p27-8-pulido-visual-accesibilidad`. Destino: `develop`.
Validación: 6 de octubre de 2026, America/Managua.

## Alcance y decisiones

| Incidencia | Resultado |
| --- | --- |
| UI-31 | `field-sizing: content` entre un mínimo cómodo y 7rem; tablas y cuadrícula aumentada alinean las columnas con su contenido más largo. Cursor y scroll propios al superar el máximo; matrices anchas usan scroll local. Vector lineal conserva su máximo de 18rem. |
| UI-32 | Dos tarjetas por fila cuando caben; matrices de seis columnas o más ocupan la fila completa. Cabecera de símbolo compacta, alturas de textarea determinadas por `rows` y expresión junto al resto del flujo. Calcular conserva su posición normal. |
| UI-33 | Agregar símbolo enfoca su Nombre; eliminar enfoca el siguiente, el anterior o Agregar. En Vectores, la primera componente de la fila correspondiente; los botones de cantidad conservan su foco. Un `role=status` anuncia el cambio. El × comparte fila y bordes completos. |
| UI-34 | Cada símbolo es un `fieldset` nombrado; sus controles dicen «Agregar una fila a A», «Eliminar símbolo B», etc. Renombrar actualiza grupo, botones y etiquetas de celdas. |
| UI-35 | Cada radio de Aplicaciones y propiedades explica su cálculo en una línea, enlazada mediante `aria-describedby`, preservando también la descripción del error. |
| UI-57 | Todas las plantillas de herramientas usan `{% disclosure %}`: chevrón primero, icono opcional de opciones, título con nivel de encabezado y detalle opcional. Solo el summary principal del procedimiento es sticky. |
| UI-62 | Labels y leyendas asociados, `--text-sm`, peso 600, misma separación hasta el control; `label_suffix=""`. Ayudas regulares, metadatos `--text-xs`, títulos de sección `--text-base`. |
| UI-65 | Token de borde específico para campos; hover, foco, error y disabled conservan sus prioridades. Los bordes de paneles mantienen su tono anterior. |
| UI-66 | Placeholder en `--color-muted`, opacidad 1; contraste medido en los campos reales de sistemas, expresiones, bases y romanos. |
| UI-67 | `scroll-padding-top` global reserva cabecera + 1.5rem; sustituye el margen genérico de anclas para evitar reserva doble. Dentro del procedimiento se añade la franja del summary; se conserva la reserva inferior del teclado. |

Se conservaron los avances locales y sus seis commits. Se completó la documentación,
la medición comparativa y el runner con ventana mínima y matriz 1×1. Sin dependencias,
cambios matemáticos, versión, tags, release ni integración a develop. No se añadió
transferencia de datos entre herramientas.

Escala nueva: `--text-xs: 0.8rem`, `--text-sm: 0.875rem`, `--text-base: 1rem`.
Borde nuevo: `--color-border-input: #858585` (claro), `#7a7a7a` (oscuro).
Los contratos de componentes quedan en [interfaz](interfaz.md); comandos y cobertura
del runner en [pruebas](pruebas.md#p278--pulido-visual-y-accesibilidad).

Se eligió CSS nativo tras comprobar `field-sizing` en el Browser integrado y en
WebView2 154. El crecimiento limitado mantiene cursor y desplazamiento nativos,
como describe [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/field-sizing).

## UI-32: comparación con develop

Misma aplicación y estado, sin resultado, ayudas plegadas, scroll inicial, fuentes
del equipo y zoom normal. Base servida desde un archivo de `c9ead90` en el puerto
8886; rama en 8885. Valores redondeados, relativos al comienzo del documento CSS;
se midió el borde superior del textarea Expresión y del botón Calcular.

| Viewport | Estado | Expresión antes → después | Calcular antes → después | Reducción de Calcular |
| --- | --- | --- | --- | --- |
| 1920×1010 | A/B iniciales, 2×2 | 826 → 696 | 1127 → 932 | 195 px, 17 % |
| 1280×650 | A/B iniciales, 2×2 | 826 → 696 | 1127 → 932 | 195 px, 17 % |
| 1920×1010 | A/B/C/D, 4×4 | 1595 → 1154 | 1896 → 1391 | 505 px, 27 % |
| 1280×650 | A/B/C/D, 4×4 | 1595 → 1154 | 1896 → 1391 | 505 px, 27 % |

En 1920×1010 el botón inicial termina en y≈975. Las cuatro matrices no caben en
el primer viewport, pero reducen claramente el desplazamiento. El ancho máximo
del contenido es el mismo en ambos tamaños; por eso sus medidas verticales coinciden.

## UI-65/UI-66: contraste final

Luminancia y ratios WCAG calculados a partir de los colores efectivos de CSS.
El runner comprueba además cada control visible y sus estados de error y foco.

| Superficie | Fondo claro | Borde claro | Fondo oscuro | Borde oscuro |
| --- | --- | --- | --- | --- |
| Raised | #ffffff | 3.69:1 | #1e1e1e | 3.88:1 |
| Surface | #fafafa | 3.54:1 | #191919 | 4.10:1 |
| Muted | #f3f3f3 | 3.33:1 | #262626 | 3.53:1 |
| Aumentada | #f0f0f0 | 3.24:1 | #2b2b2b | 3.30:1 |

Los placeholders usan `#626262` en claro y `#adadad` en oscuro. Sobre el fondo
de sus campos: **5.49–6.10:1** en claro y **6.74–7.43:1** en oscuro. Incluso en
la superficie aumentada, sin placeholders actualmente, el token daría 5.35:1 y
6.31:1. Ningún control activo probado queda debajo de 3:1 ni ningún placeholder
probado debajo de 4.5:1.

## QA renderizada y foco

QA principal: **@Browser integrado**, sin fallback a Playwright externo. Se
comprobaron identidad de página, contenido significativo, ausencia de overlays,
consola y cambios de estado mediante DOM/AX, geometría y screenshots.

| Viewport CSS | Claro | Oscuro | Overflow horizontal de página |
| --- | --- | --- | --- |
| 1920×1010 | 7 herramientas | 7 herramientas | ninguno |
| 1280×650 | 7 herramientas | 7 herramientas | ninguno |
| 1084×721 | 7 herramientas | 7 herramientas | ninguno |
| 744×521 | 7 herramientas | 7 herramientas | ninguno |
| 390×650 | 7 herramientas | 7 herramientas | ninguno |
| 760×560, mínimo desktop | 7 herramientas | 7 herramientas | ninguno |

Las herramientas son Operaciones, Inversa, Vectores, Reducción, Ax=b, Bases y
Romanos: 84 combinaciones renderizadas. Los scrolls de matrices siguen siendo locales.

Pruebas de interacción adicionales:

- A 390 px, Agregar símbolo C enfoca `id_nombre_2` y anuncia «Se agregó el símbolo
  C.»; eliminar B enfoca el Nombre de C reindexado y anuncia la baja. El runner
  cubre también eliminar último y único, y alta/baja de vectores preservando datos.
- AX identifica «Símbolo A/B» y cada botón. Renombrar A→M cambia grupo, botones y
  labels de celdas; el input conserva su label real.
- `-11/13`, `123/456`, `-123456` y `3.14159` tienen `scrollWidth == clientWidth`
  en las celdas probadas. El runner cubre tablas, matriz aumentada y vectores,
  matriz 1×1, una 10×10, máximo de ancho, selección del cursor y scroll local.
- Shift+Tab real desde la primera celda de Inversa tras PageDown, a 1084×721,
  devuelve al botón + con `:focus-visible`, top≈198 frente a cabecera de 56 px.
  La vuelta posterior a las migas las deja en y≈81. Se dejaron terminar los
  desplazamientos nativos antes de medir.
- El runner comprueba ancla `#resultado`, foco tras scroll y foco en un
  subdisclosure bajo el summary sticky. Solo el principal mantiene `position:sticky`.
- Las cinco ayudas de Inversa están visibles y asociadas; abrir/cerrar los
  disclosures conserva estado y funcionamiento nativo.

Comprobación complementaria en **WebView2 154**, con pywebview existente y ventana
oculta temporal: runner P27.8, **16/16**. Ventana externa mínima 760×560; área CSS
746×523, documento 731/731 px. A zoom 125 %, área 597×418 y documento 584/584 px.

**High contrast básico:** `forced-colors:active` emulado mediante el protocolo de
WebView2, con foco de documento emulado porque la ventana estaba oculta. Input con
foco visible y outline sólido de color de sistema, borde de sistema, fondo blanco,
fracción completa, chevrón conservado y sin overflow. No se cambió el tema de
contraste de Windows ni se pretende una validación completa de UI-68.

## Evidencias

Screenshots y JSON de medidas quedan fuera del repositorio en la carpeta `p278`
del artefacto local de esta conversación. La entrega incluye capturas del estado
inicial, cuatro símbolos, fracciones, foco dinámico, Inversa con ayudas y ambos
temas a 390 px. No se añaden capturas ni scripts temporales a las fuentes.

## Pruebas automáticas y regresiones

| Comando | Resultado |
| --- | --- |
| `uv run --locked python --version` | Python 3.13.3 |
| `uv run --locked python -m unittest discover -v` | 1615 pruebas, OK; 118.896 s |
| `uv run --locked python manage.py check` | Sin problemas, 0 silenciados |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK |
| `uv lock --check` | OK, 30 paquetes |
| `git diff --check` | OK |

Runners ejecutados en @Browser, con scripts de producción y POST de Django donde
corresponde; no se cambian las dependencias ni se simula la aritmética:

| Runner | Casos aprobados |
| --- | --- |
| `pulido_browser` | 16/16 |
| `entradas_browser` | 19/19 |
| `operandos_browser` | 15/15 |
| `inversa_browser` | 7/7 |
| `teclado_browser` | 30/30 |
| `feedback_browser` | 19/19 |
| `buscador_browser` | 16/16 |
| `presentacion_browser` | 10/10 |
| `resultado_browser` | 66/66 |
| `escritorio_browser` | 27/27 |
| **Total** | **225/225** |

Se comprobó la sintaxis con `node --check` de los scripts de matrices, vectores,
expresiones y los runners modificados. El runner del buscador dejó de exigir
exactamente `3px` de contorno: mantiene las comprobaciones de foco real, estilo
sólido y ancho positivo, tolerando el escalado de pantalla (`2.66667px`).

Regresiones cubiertas: P27.1 dimensiones, entradas dinámicas y preservación de
datos; P27.3 destino contextual y dock del teclado; P27.4 errores, busy,
confirmaciones y submitter; P27.5 buscador y menú; P27.6 scroll de matrices,
stale, resultado y summary sticky; P27.7 preferencias, menú contextual mediante
eventos, Alt+flechas y páginas de error. Los últimos son contratos DOM, no una
prueba de instalación ni del menú nativo de Windows.

Consola: las 84 combinaciones de herramientas no produjeron errores. En el runner
de resultados se registró un `MutationObserver.observe` con nodo inválido durante
la carga de iframes; aun así pasó 66/66. No se reprodujo en las páginas normales
ni al abrir directamente su resultado de Inversa. `presentacion.js` conserva el
código de develop; el registro se documenta sin atribuirlo a un defecto nuevo.

## Archivos modificados

Lista de los 32 archivos respecto a `c9ead90`, incluida esta validación:

```text
docs/interfaz.md
docs/pruebas.md
docs/validacion-p27-8.md
frontend/web/calculadora/forms_expresiones.py
frontend/web/calculadora/forms_feedback.py
frontend/web/calculadora/forms_inversa.py
frontend/web/calculadora/servicios_inversa.py
frontend/web/calculadora/static/calculadora/expresiones.js
frontend/web/calculadora/static/calculadora/matriz.js
frontend/web/calculadora/static/calculadora/styles/base.css
frontend/web/calculadora/static/calculadora/styles/components.css
frontend/web/calculadora/static/calculadora/styles/modules.css
frontend/web/calculadora/static/calculadora/styles/tokens.css
frontend/web/calculadora/static/calculadora/vectores.js
frontend/web/calculadora/templates/calculadora/components/disclosure.html
frontend/web/calculadora/templates/calculadora/modules/expresiones/_simbolo.html
frontend/web/calculadora/templates/calculadora/modules/expresiones/_simbolo_plantilla.html
frontend/web/calculadora/templates/calculadora/modules/expresiones/index.html
frontend/web/calculadora/templates/calculadora/modules/inversa/index.html
frontend/web/calculadora/templates/calculadora/modules/matrices/_producto_columnas.html
frontend/web/calculadora/templates/calculadora/modules/matrices/_producto_fila_columna.html
frontend/web/calculadora/templates/calculadora/modules/sistemas/index.html
frontend/web/calculadora/templates/calculadora/modules/vectores/index.html
frontend/web/calculadora/templatetags/componentes.py
tests/buscador_browser.js
tests/inversa_browser.js
tests/pulido_browser.js
tests/pulido_browser.py
tests/test_expresiones_matriciales_web.py
tests/test_multiplicacion_matrices_web.py
tests/test_procedimiento_plegable.py
tests/test_propiedades_inversa_web.py
```

## Commits

Se conserva la secuencia local existente:

- `20c8a33`: etiquetas, bordes y placeholders.
- `3ba96b9`: lectura completa de celdas.
- `5ab1f9e`: disclosures y ayudas de Inversa.
- `59a1422`: compactación y foco dinámico.
- `eb4cf3d`: foco visible bajo la cabecera.
- `3557345`: runner P27.8 y ajustes de integración.
- `60a2eec`: ventana mínima, matriz 1×1 y contorno de foco sin píxel exacto.

La documentación e informe se guardan en un commit final independiente.

## Límites

- En navegadores antiguos sin `field-sizing` se conserva el ancho fijo; la
  comprobación de lectura completa corresponde a Chromium y WebView2 probados.
- Zoom y high contrast se comprobaron en el runtime; no con un lector de pantalla
  ni con los temas físicos de contraste de Windows.
- No se repitió instalación/build Windows ni interacción nativa del menú contextual.
  Desktop/build no cambian; sus contratos se verifican con pruebas existentes.
