# Copiado matricial de entrada (P28.2)

`copiar_matricial.js` consume inmediatamente `seleccionMatricial.activa()` de
[P28.1](seleccion-matricial.md): `celdas`, `input.value`, `limites` y `rectangular`.
No guarda otro modelo ni vuelve a decidir qué pertenece a A o b. Los siete
comandos, rangos Shift y conjuntos Ctrl pasan por la misma serialización.
La plantilla compartida carga el módulo después del de selección, exclusivamente
en Operaciones, Inversa, Ax=b y Reducción. No cambia CSS, backend ni dependencias.

## Acción de copia y prioridad textual

Un listener de `copy` en `document` escribe mediante `clipboardData.setData` y
cancela la acción nativa solo al completar la copia matricial. Funciona con Ctrl+C
y con cualquier acción del menú nativo que emita ese evento. No escucha Ctrl+C
por separado, no usa `navigator.clipboard.write`, no modifica `cut` y no toca el
portapapeles al seleccionar, editar o cargar la página.

Si el elemento enfocado o el destino del evento tiene `selectionStart` distinto
de `selectionEnd`, o existe texto seleccionado en la página, prevalece la copia
nativa. Esto incluye inputs ajenos a la matriz y textarea. Sin selección
matricial, sin `clipboardData` o con evento previamente cancelado tampoco se
intercepta. Una selección matricial 1×1 sigue produciendo los tres formatos,
incluso si su valor es vacío. Shift+flechas conserva el contrato de selección
P28.1; Ctrl+A dentro del input permite seleccionar su texto y copiarlo normalmente.

La copia conserva foco, valores, selección y estado del resultado; no emite
`input` ni envía formularios. Se reutiliza una sola región `data-estado-seleccion`
con `role=status`, `aria-live=polite` y `aria-atomic=true`: “4 celdas copiadas.”.
Cada acción actualiza esa región, sin otro anuncio ni modal.

WebView2 ya filtra su menú a Cortar/Copiar/Pegar/Seleccionar todo mediante
`desktop.filter_context_menu`; no se modifica ese filtro ni la disponibilidad
nativa de Copiar cuando no hay texto seleccionado. Se garantiza la ruta común
cuando el menú dispare `copy`, no que el motor habilite esa opción en todo contexto.

## Tres formatos simultáneos

| Tipo | Contenido |
| --- | --- |
| `text/plain` | Rectángulo contenedor, TAB entre columnas, LF entre filas, sin terminador añadido. |
| `text/html` | Una tabla con `tr`/`td`, misma geometría, contenido escapado y fracciones numéricas como fórmulas aritméticas. |
| `application/x-pygebra-matrix-selection` | JSON v1 de geometría relativa; única fuente de verdad para la máscara copiada. |

El tipo propio es estable, en minúsculas y sin prefijo `web `: este último
pertenece a la API asíncrona, no al `DataTransfer` del evento. Chromium transporta
los tipos no estándar como datos personalizados de DataTransfer junto al texto
y HTML ([implementación de Chromium](https://chromium.googlesource.com/chromium/src/+/15ef0750482972d738ff7b8d278950ff3d02ee29/third_party/blink/renderer/core/clipboard/system_clipboard.cc)).
P28.0 fue probado manualmente en WebView2 por Erving antes de este incremento.
El software que no reconozca el tipo propio puede usar los formatos estándar.
No se duplica metadata en sessionStorage, localStorage, HTML ni texto.

Los valores vienen de `input.value`: no se convierten, simplifican, recortan ni
leen desde el formato Decimal de resultados. Los huecos de una selección
irregular se escriben como celdas vacías. Una diagonal 3×3 contiene:

```text
1\t\t\n\t5\t\n\t\t9
```

Una celda seleccionada vacía y un hueco tienen el mismo texto vacío; únicamente
`celdas` en la metadata decide cuál está seleccionada. No se leen valores de
las posiciones ajenas al conjunto.

## HTML para Excel

La auditoría previa P27/P28, confirmada por Erving en esta sesión, comprobó que
`<td>=1/2</td>` se recibe como cociente matemático en Excel y evita la fecha que
puede producir `1/2` como texto. Se elige esa variante mínima, sin `x:num`,
namespace Office, conversión a float, atributos de geometría ni estilos visuales.
Microsoft describe la [conversión automática de fracciones en fechas](https://support.microsoft.com/en-us/excel/display-numbers-as-fractions).

| Entrada | Celda HTML | Tratamiento |
| --- | --- | --- |
| `-2` | `<td>-2</td>` | Entero literal. |
| `3.1400` | `<td>3.1400</td>` | Decimal literal; sin redondear ni cambiar separador. |
| `2/4` | `<td>=2/4</td>` | División, sin sustituir por `0.5` ni simplificar a `1/2`. |
| ` -11 / 13 ` | `<td>= -11 / 13 </td>` | Conserva los espacios y el valor original después de `=`. |
| vacío/hueco | `<td></td>` | Conserva posición; la distinción vive en la metadata. |
| caracteres especiales/texto | `td` con texto escapado | `&`, `<`, `>`, comillas y apóstrofes se escapan. |

Solo se añade `=` a fracciones ASCII con signo opcional inicial, hasta 100
dígitos por componente, espacios alrededor y denominador no nulo. Fracciones
inválidas y otro texto se conservan escapados con `mso-number-format:'\@'`,
un formato de dato textual, para evitar que se ejecuten como fórmulas de la hoja
destino. No se ejecuta ni evalúa código al copiar. La importación de hojas de
cálculo usa su precisión y configuración regional: esto evita fechas para las
fracciones, pero no convierte Excel en un motor de racionales arbitrarios.
TSV sigue transportando el literal exacto completo.

## Esquema v1 y validación para P28.3

```json
{"version":1,"filas":3,"columnas":3,"forma":"mascara","celdas":[[0,0],[1,1],[2,2]]}
```

| Campo | Contrato |
| --- | --- |
| `version` | Entero `1`; otras versiones se rechazan. |
| `filas`, `columnas` | Dimensiones positivas del rectángulo mínimo copiado. |
| `forma` | `rectangulo` si están todas las posiciones; `mascara` si existen huecos. Describe geometría, no el comando de origen. |
| `celdas` | Array no vacío de pares `[fila, columna]`, enteros desde cero relativos al rectángulo, estrictamente ordenados por fila y luego columna. |

Rectángulos también enumeran todas sus posiciones. No se incluyen valores,
HTML, nombre de matriz, coordenadas originales, comando, estado UI ni DOM.
La forma se comprueba contra la cantidad efectiva: no se confía en la etiqueta.

`window.copiadoMatricial` expone `TIPO`, `serializar(snapshot)` y
`parsear(metadata, texto)`. Serializar devuelve `{texto, html, metadata}` o
`null` si no es representable. Parsear devuelve los cinco campos validados o
`null`; no cambia el DOM y **no está conectado a paste**.

Límites del protocolo v1:

- Hasta 12 filas, 13 columnas y **120 posiciones en el rectángulo**, coherentes
  con el máximo de Reducción, incluida b. Por ejemplo 12×10 y 9×13 son válidos;
  12×13 no lo es. El destino futuro deberá comprobar además sus propios límites.
- Metadata: **4096 bytes UTF-8**. Enumerar 120 pares necesita menos de 1 KiB en
  la salida compacta; 4 KiB deja margen y limita el trabajo de JSON.parse.
- TSV: **65536 bytes UTF-8**, suficiente para 120 fracciones de dos componentes
  de 100 dígitos, con margen. Se limita longitud antes de codificar y bytes antes
  de parsear/separar. Ambos límites acotan el conjunto a 68 KiB.

Se rechazan JSON inválido, raíces/campos erróneos o extras, versiones desconocidas,
dimensiones no enteras/fuera de límites, área excesiva, pares mal formados,
coordenadas negativas, fuera del rectángulo, repetidas o fuera de orden, conjuntos
vacíos/excesivos, forma incoherente y rectángulos que no sean mínimos.
El TSV debe tener exactamente esas filas y columnas; todo hueco debe estar vacío.
Se acepta LF o CRLF, pero no CR aislado; no se recortan filas exteriores ni valores,
porque pueden representar celdas seleccionadas vacías. Tabs o saltos dentro de
un valor no son representables y se rechazan al serializar.

La metadata no autentica al emisor: cualquier página puede escribir ese tipo.
La coherencia significa forma/dimensiones/huecos compatibles con el TSV. No
prueba la procedencia ni detecta un cambio en valores seleccionados que preserve
esas propiedades; no transporta un segundo ejemplar de los valores ni una firma.
La validación de números y capacidad del destino seguirá siendo necesaria en P28.3.

Si no se pueden generar los formatos o escribirlos, se anuncia el fallo sin éxito
parcial; no se cancela la copia nativa. En un fallo de escritura se limpia el
DataTransfer del evento. No se promete conservar el portapapeles anterior si el
motor efectúa la acción nativa.

Para P28.3: metadata ausente, desconocida o inválida debe ignorarse y dar paso al
fallback rectangular de texto existente. **Nunca se debe deducir la máscara de
los vacíos de TSV.** P28.2 mantiene el paste P27, incluidos su recorte de líneas
vacías exteriores, destino desde una celda y validaciones atómicas; por ello
todavía no promete restaurar máscaras ni rellenar selecciones.

Pruebas y límites de QA: [validación P28.2](validacion-p28-2.md).
