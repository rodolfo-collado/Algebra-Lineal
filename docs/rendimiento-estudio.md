# Rendimiento y respuesta de Estudio

[Índice](README.md) · [Pruebas](pruebas.md)

Intervención sobre `origin/develop` `5096e0e`, con el PR #113 integrado. Una rama
`feature/fluidez-estudio`, sin cambios de versión, algoritmos ni dependencias del producto.

## Diagnóstico

- **Espera intencional:** la captura de la cámara duraba 900 ms; el diorama,
  600 ms; la entrada global, 420 ms. Esta última también alcanzaba a Minimalista.
  Además se animaban otra vez los bloques del contenido, con retardos escalonados.
- **Clics perdidos:** `root` y la cabecera participaban en View Transitions.
  Sus controles eran imágenes durante la animación. En WebView2, un clic sobre
  Opciones a los 63 ms alcanzó `<html>` y no abrió el reproductor.
- **Renderizado repetido:** luces, vapor y cursor animaban el SVG de la habitación
  incluso al bajar al catálogo. Una traza de 2,5 s en oscuro registró unos 71 ms
  de `Paint` y 55 ms de `UpdateLayoutTree` en ese estado. Pausar el ambiente eliminó
  ambos trabajos repetidos. La bienvenida conserva estas animaciones.
- **Audio:** en un perfil de entrada, abrir `AudioContext` tomó 52 ms y preparar
  Café, 29 ms adicionales, en la misma tarea. La composición de cada compás tomó
  aproximadamente 0,1–1,9 ms. El temporizador de programación de un segundo no es
  una espera impuesta a la navegación. El fundido musical entre documentos
  (1,5 s) tampoco bloquea los controles y se conserva.
- **Explorador y componentes:** los 90 ms del hover son intención del puntero;
  clic y teclado no esperan ese temporizador. `explorador.js` fuerza layout para
  repetir dos gestos; durante las navegaciones de WebView2 sin música no se
  encontraron tareas largas que justificaran reescribirlo. `historial.js` y
  `navigation.js` llaman al historial nativo; el rail
  lee su geometría una vez. `presentacion.js` ya agrupa sus lecturas en un frame.

Se contrastaron por separado cámara sin transformación, cámara sin desenfoque y
cabecera/índice sin `backdrop-filter`. No dieron una reducción consistente del
trabajo de pintura en reposo: por ejemplo, quitar el desenfoque del catálogo dio
99 ms de `Paint` frente a 71 ms de referencia. No se conservó ninguna de esas
supresiones. Estas pruebas no demuestran que los filtros sean gratis en otras GPU.

## Cambios

- Solo el diorama decorativo se captura; `root`, la cabecera y la habitación no.
  La capa de transición deja pasar el puntero. Un diorama que sale sin pareja se
  oculta para no cubrir los campos de la herramienta siguiente.
- La cámara conserva el viaje mediante `@starting-style` y su transición CSS,
  detrás del contenido. Se recuerda únicamente su transformación y filtro en la
  sesión; sin almacenamiento o sin soporte, aparece directamente en su destino.
  Se descartó capturar el fondo sin `root`: su imagen cubría la interfaz viva.
- Viajes de hasta 280 ms y un fundido de contenido de 180 ms, sin entradas
  escalonadas adicionales. El contenedor del teclado fijo no se transforma.
- El ambiente se pausa también al bajar al catálogo y se reanuda al volver a la
  bienvenida. Se mantienen las escenas, colores, desenfoques y gestos del índice.
- Abrir el dispositivo de audio y sintetizar las muestras se ejecutan en turnos
  separados. Pausar u ocultar la ventana cancela la preparación pendiente y
  suspende el contexto cuando corresponde. No cambian las partituras ni las muestras.
- `prefers-reduced-motion` sigue desactivando viajes, animaciones y transiciones.

## Medición reproducible

Windows, Intel i5-1145G7, Iris Xe, WebView2/Edge 157.0.4341.42. Viewport de
1280 × 698 CSS, escala 1,5, sin limitación artificial de CPU o red. WebView2 ejecuta
`desktop.py` con Waitress y preferencias aisladas; Edge abre ese mismo servidor.
Música: Café al 40 %, con los efectos de selección apagados. No se comparan los
tiempos del servidor de un motor contra los del otro.

Cada combinación de estilo, tema y música repite dos veces Inicio → Álgebra lineal
→ Determinantes → Atrás → Adelante: ocho muestras por combinación y referencia.
El ejecutor usa clics de ratón, sin esperar que termine la animación para probar
Opciones; con `--validar` también encadena saltos rápidos, escribe en una celda,
comprueba el dock y repite un salto con movimiento reducido.

`vistaFinal` mide desde `pagereveal` hasta el final más tardío de la captura, el
viaje CSS de la cámara y el fundido de contenido. En la base el límite lo imponía
`ViewTransition.finished` (campo `transicion`). No es el tiempo total desde el clic
ni el tiempo del servidor; los gestos internos de los objetos del diorama siguen
siendo independientes. Se registran TTFB y DOMContentLoaded
aparte. `huecosRAF` estima intervalos perdidos respecto a 60 Hz durante el segundo
de llegada: incluye la pausa inicial de captura y no equivale al contador de
fotogramas descartados por la GPU. Las tareas largas son entradas de al menos 50 ms
del PerformanceObserver, incluyendo el arranque del audio. `Paint` de las trazas
mide trabajo de CPU, no tiempo de GPU ni consumo de energía.

El plugin Browser y Chrome DevTools MCP no estaban disponibles. Playwright
automatiza los clics y recoge estas métricas; el arnés usa su versión 1.64.1
temporal, sin añadirla a `pyproject.toml` o `uv.lock`, y CDP para WebView2 real.

Iniciar una instancia de diagnóstico con `ALGEBRA_PREFERENCIAS` apuntando a un
archivo temporal y `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` igual a
`--remote-debugging-port=9333 --autoplay-policy=no-user-gesture-required`, mediante
`uv run --locked python desktop.py`. Desde la raíz del mismo worktree aislado:

```powershell
$mediciones = Join-Path $env:TEMP 'pygebra-fluidez'
New-Item -ItemType Directory -Force $mediciones | Out-Null
Copy-Item tests/fluidez_browser.py "$mediciones/fluidez_browser.py"
# Con la instancia de referencia 5096e0e abierta:
uv run --locked --with playwright==1.64.1 python "$mediciones/fluidez_browser.py" --cdp http://127.0.0.1:9333 --muestras 2 --salida "$mediciones/antes.json"
# Cerrar y reiniciar la instancia con los archivos optimizados antes de continuar:
uv run --locked --with playwright==1.64.1 python "$mediciones/fluidez_browser.py" --cdp http://127.0.0.1:9333 --muestras 2 --validar --salida "$mediciones/despues.json"
```

Ambas referencias calientan los recursos antes de medir, con la caché normal del
navegador y sin interceptar CSS. Se descartaron ensayos con caché desactivada o
CSS interceptado: Edge omitía la transición por `ViewTransition opt-in disabled`,
así que no medían la misma animación. Las omisiones ocasionales de la API se
registran aparte y no se cuentan como animaciones de cero milisegundos al comparar.
El arnés no importa módulos de la aplicación: puede ejecutarse desde esa copia
temporal contra ambas referencias. Si se reproducen mediante archivos temporales
en el mismo worktree, respaldar y restaurar `estudio.css`, `musica.js` y
`frontend/web/calculadora/templates/calculadora/components/tema_inicial.html`, reiniciando `desktop.py` al
cambiar la plantilla: Django la guarda en memoria. Para Edge, sustituir `--cdp`
por `--url` con la URL de esa instancia (visible en `/json/list` del puerto 9333).
El permiso de autoplay permite comparar
la música realmente activa en cada carga. La activación por gesto se verifica
aparte mediante los controles reales. Cerrar esa instancia al acabar.

## Resultados y límites

Medianas de los recorridos. Cada flecha indica **antes → después**. La última
columna suma la duración de las tareas de al menos 50 ms por llegada y toma su
mediana; no cuenta las tareas cortas ni representa todo el tiempo de CPU.

| WebView2 | Tema | Música | Viaje de página (ms) | Huecos RAF estimados | Tareas largas (ms) |
|---|---|---|---:|---:|---:|
| Estudio | Claro | No | 924,4 → 283,2 | 12,5 → 0 | 0 → 0 |
| Estudio | Claro | Sí | 925,2 → 282,9 | 14 → 0 | 97 → 0 |
| Estudio | Oscuro | No | 937,2 → 283,7 | 33 → 0 | 0 → 0 |
| Estudio | Oscuro | Sí | 942,2 → 283,2 | 37 → 0 | 182 → 0 |
| Minimalista | Claro | No | 432,8 → 16,3 | 0 → 0 | 0 → 0 |
| Minimalista | Claro | Sí | 433,0 → 16,1 | 0 → 0 | 62 → 0 |
| Minimalista | Oscuro | No | 432,5 → 16,1 | 0 → 0 | 0 → 0 |
| Minimalista | Oscuro | Sí | 432,7 → 16,4 | 0 → 0 | 65,5 → 0 |

| Edge | Tema | Música | Viaje de página (ms) | Huecos RAF estimados | Tareas largas (ms) |
|---|---|---|---:|---:|---:|
| Estudio | Claro | No | 958,4 → 296,2 | 17 → 0,5 | 0 → 0 |
| Estudio | Claro | Sí | 951,8 → 294,0 | 23,5 → 5 | 95,5 → 0 |
| Estudio | Oscuro | No | 1033,3 → 294,0 | 36,5 → 1 | 0 → 0 |
| Estudio | Oscuro | Sí | 993,1 → 295,4 | 47,5 → 6 | 204,5 → 0 |
| Minimalista | Claro | No | 435,7 → 10,1 | 0 → 0 | 0 → 0 |
| Minimalista | Claro | Sí | 443,1 → 68,7 | 5 → 4 | 82 → 0 |
| Minimalista | Oscuro | No | 436,1 → 10,1 | 0 → 0 | 0 → 0 |
| Minimalista | Oscuro | Sí | 439,4 → 62,2 | 5 → 3,5 | 81,5 → 0 |

Se intentaron 64 navegaciones por referencia y motor. Una transición de la base
en Edge fue omitida por la API; esa muestra de duración cero se excluye de las
medianas de su fila (7 muestras frente a 8). El resto usa 8. Después del cambio
hubo cuatro tareas de 50–51 ms en Edge y dos de 50–63 ms en WebView2: las medianas
de cero no significan ausencia absoluta de bloqueos.

En WebView2, Estudio acorta aproximadamente un 70 % el viaje de página. El clic real
sobre Opciones a los ~50 ms de estar lista la vista falló en las ocho combinaciones
de referencia y pasó en las ocho optimizadas, en ambos motores. También pasaron
los saltos rápidos, Atrás/Adelante, la entrada `1/2` en una celda con dock visible y
el salto con movimiento reducido. Las ejecuciones optimizadas no registraron
excepciones JavaScript ni omisiones de la transición.

Con el mismo CSS optimizado, cinco pares de recargas alternando solo el reproductor
original y el separado dieron un bloqueo máximo por recarga de 96–199 ms frente
a 59–80 ms; medianas de **102 → 78 ms**. Esto verifica la mejora del audio por
separado, sin atribuirle toda la ganancia de la navegación.

Las capturas durante el viaje verifican que cabecera, índice y botón Abrir siguen
visibles mientras la cámara interpola su posición. Se mantiene el diorama y el
ambiente de la bienvenida. No se afirma que todos los recorridos alcancen 60 FPS:
el indicador RAF es aproximado y Edge conserva algunos intervalos largos.

Para separar la carga de esa espera visual, las medianas globales de TTFB fueron
13,4 → 12,5 ms en WebView2 y 23,1 → 19,4 ms en Edge; DOMContentLoaded,
75,7 → 52,5 ms y 99,0 → 82,2 ms, respectivamente. El servidor no se modificó.

Regresiones DOM por estilo y motor: Bisección 19/19, Conjuntos 14/14, buscador y
reproductor 21/21, entradas 19/19 y teclado 36/36. Se repiten en Estudio y
Minimalista, en WebView2 real y Edge: 436 comprobaciones. Los arneses corrigen la
expectativa antigua de Conjuntos bloqueado y seleccionan explícitamente la
herramienta del panel para no depender de lo recordado en otra ejecución.
Se comprobó también un cálculo real de `x^2-2`, anterior/siguiente/pausa del
reproductor y el dock a 390 × 844, sin desborde horizontal ni excepciones JS.
La suite completa local pasó 1.958 pruebas, junto con Django, compilación,
lockfile y `git diff --check`.

No se han medido equipos de menor potencia, GPU diferentes, lector de pantalla,
táctil físico ni consumo energético. La apertura nativa del dispositivo de audio
puede seguir produciendo una tarea larga; separar los turnos no elimina ese costo.

La regla de interactividad sigue la [guía de Chrome sobre capturas y controles](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/group-element-transitions).
Los eventos y la omisión de transiciones se describen en la [documentación entre documentos](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document).
La entrada CSS usa [@starting-style](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/animate-element-entry-exit).
