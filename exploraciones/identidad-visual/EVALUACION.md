# Evaluación del estudio visual

20 de octubre de 2026. `frontend-design` orientó la diferenciación de conceptos;
`web-design-guidelines` se aplicó con las
[reglas vigentes consultadas](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md).
No es una certificación de accesibilidad ni un estudio con usuarios.

## Entorno y resultados

- Navegador integrado de Codex (Chromium), HTTP en loopback: puerto 8865 para
  observación del producto y 8866 para prototipos. Inspección DOM, foco y capturas.
- 49 aserciones directas: bienvenida → áreas → buscar matrices → herramienta;
  tres ejemplos en tres conceptos; foco; siguiente/anterior; extremos; formato
  exacto/decimal; cambio de ejemplo; sonido activado/silenciado; Tab, Enter y Space;
  búsqueda sin coincidencias. [Registro](evidencias/qa-browser.json).
- 54/54 comprobaciones reproducibles en [pruebas.html](pruebas.html). Se ejercita
  el controlador real dentro de iframes del mismo servidor. Complementa, no
  sustituye, el recorrido con teclado real del navegador.
- 36/36 combinaciones sin overflow de página: 3 conceptos × 3 pantallas ×
  320 × 650, 390 × 844, 760 × 560 y 1100 × 760. También se verificó herramienta a
  1440 × 900. Se compararon `scrollWidth` y `clientWidth`, sin esconder el overflow.
  [Registro](evidencias/qa-responsive.json). Las capturas móviles incluyen resultado;
  las de desktop muestran las tres pantallas a 1440 × 900.
- 24/24 pares de tokens sólidos: texto normal ≥ 4.5:1; bordes de campo/foco ≥ 3:1.
  [Datos](evidencias/qa-contraste.json). Texto secundario sobre superficies probadas:
  mínimo 5.11:1 en Patio, 5.62:1 en Trama y 5.79:1 en Prisma.
  Se revisaron además ilustraciones y hover visualmente; el script no audita todos
  los estados, pseudoelementos, antialiasing o combinaciones posibles del DOM.
- Consola del recorrido directo: sin warnings ni errores registrados.
- JS: `node --check` en `prototipo.js` y `pruebas.js`, aprobado.
- Proyecto: Django check sin incidencias, compileall aprobado, lockfile aprobado,
  `git diff --check` aprobado. No se ejecutó build ni instalador porque el estudio
  no cambia distribución.
- Suite general, primer intento en sandbox: **FAILED**, 1862 pruebas en 136.629 s,
  3 fallos y 125 errores. Aparecieron permisos denegados en temporales de
  preferencias/descargas, sockets y MSYS de Git. No se presenta ese intento como éxito.
- Repetición con permisos normales: **OK**, 1862 pruebas en 186.212 s, exit code 0.
  El log completo queda local en `build/exploracion-suite.log` (ignorado por Git).
  `uv lock --check` también se repitió correctamente tras un fallo de caché del sandbox.
- La comprobación inicial de teclado usó una opción de locator no soportada
  (`level`) y resultó ambigua al aparecer varios títulos; se corrigió el locator
  por nombre y el recorrido Tab/Enter/Space pasó. Fue un fallo del guion de QA.

## Revisión por archivo

### `prototipo.js`

- `prototipo.js:47` — corregido: contenedor del texto de área usa `div`, compatible
  con encabezado y párrafo; nombres completos junto a símbolos decorativos.
- `prototipo.js:99` — corregido durante QA: foco al título de la pantalla visible,
  sin seleccionar por accidente un encabezado oculto. Navegación y áreas usan hash;
  los enlaces conservan historial y apertura por separado.
- `prototipo.js:26` — controles de audio con nombre/estado, inicio apagado,
  síntesis local y salida silenciosa si Web Audio falla. Una comprobación posterior
  a `resume()` evita programar tonos si se silenció durante la activación.
- `prototipo.js:54` — **limitación aceptada:** la consulta escrita del buscador no
  se serializa en la URL; sí se enlaza el área de destino.
- `prototipo.js:99` — **limitación aceptada:** ejemplo seleccionado, entrada del
  procedimiento y formato no sobreviven a recarga ni tienen enlace profundo.
  En un estudio de flujo acotado no se añadió un router de estado completo.
- Etiquetas y nombres en inputs/select; celdas explícitamente de solo lectura;
  resultado con descripción por filas; acciones nativas; regiones con títulos;
  estado dinámico anunciado mediante `role=status`. Sin captura global de teclas,
  trampas de foco, pegado bloqueado ni gestos obligatorios.

### `base.css`

- `base.css:113` — corregido: hover de primario y de estado seleccionado mantiene
  contraste; el texto blanco ya no queda sobre un fondo pálido.
- `base.css:118` — corregido: skip link fuera del flujo mediante posición absoluta;
  evita el artefacto de un enlace fijo fuera de pantalla en capturas de página larga.
- `base.css:120` — entrada corta con transform, contenido opaco desde el primer
  fotograma; navegación inmediata e interrumpible.
- `base.css:151` — regla de movimiento reducido desactiva animaciones/transiciones;
  comprobación de fuente/CSSOM, **sin emular el cambio de preferencia del sistema**.
- Foco visible, tablas numéricas con cifras tabulares, botones ≥44 px en los
  controles de cálculo, wrapping y breakpoints sin scroll horizontal de página.

### `conceptos.css`

- Layouts diferenciados; lectura móvil entrada → procedimiento → resultado.
- Prisma declara `color-scheme:dark` en raíz y controles con fondo/texto explícitos.
- Colores acompañados por nombre, posición y estado textual; la selección de
  resultado tiene contorno. Estilos de colores forzados definidos, sin emulación
  de alto contraste ni validación física de Windows.
- **Pendiente:** evaluar cada identidad en el tema opuesto. Los tres conceptos no
  equivalen a tres temas instalables sobre las calculadoras reales.

### `index.html` y `comparador.css`

- Enlaces reales a cada pantalla, jerarquía de títulos, skip link, imágenes con
  dimensiones y decoración con alt vacío. Previews propios de CSS/SVG, sin
  imágenes externas ni material de las referencias.
- Comparación abierta; no se fuerza un ganador por tamaño de botón o posición
  privilegiada. El orden del estudio no sustituye la prueba con orden alternado.

## Qué permanece sin verificar

1. **WebView2 nativo, navegación desktop y empaquetado:** inspeccionados en código,
   sin lanzar una distribución ni instalar el prototipo dentro de la app.
2. **Lectores de pantalla reales:** estructura DOM comprobada, sin sesión de NVDA,
   JAWS o VoiceOver. No se atribuye una conformidad WCAG completa.
3. **Audio físico:** botones/estado y programación Web Audio revisados y recorridos;
   no se certificó audibilidad, comodidad, latencia del dispositivo o nivel acústico.
4. **Movimiento reducido y colores forzados:** reglas revisadas, sin cambiar ni
   emular preferencias del sistema. Es necesario un smoke con esas preferencias.
5. **Otros navegadores, zoom 200/400 %, dispositivos táctiles físicos y fuentes
   alternativas:** fuera de esta ejecución. La anchura móvil se emuló con viewport,
   no con un teléfono real. El modo `file://` tampoco forma parte del recorrido probado.
6. **Escala real y edición:** ejemplos 2 × 2 y tres operaciones. No se verifican
   matrices grandes, fracciones largas, errores de usuario, pegado, presupuestos,
   todas las herramientas ni una sesión larga. Las fixtures no prueban el motor.
7. **Resultados de uso:** sin entrevistas, tiempos comparados, carga cognitiva
   medida ni validación de la recomendación con estudiantes.

## Repetir los checks

```powershell
# Desde la raíz, con el servidor estático ya iniciado:
node --check exploraciones/identidad-visual/prototipo.js
node --check exploraciones/identidad-visual/pruebas.js
.venv\Scripts\python.exe exploraciones/identidad-visual/verificar_contraste.py
```

Abre `http://127.0.0.1:8866/exploraciones/identidad-visual/pruebas.html` y ejecuta el
botón. Para teclado: desde bienvenida llega a la entrada con Tab, actívala con
Enter, busca Matrices y abre el procedimiento; usa Enter en Siguiente y Space en
Ver el procedimiento completo. Comprueba foco visible, audio apagado al abrir y
silenciado al pulsar de nuevo. Cambia el ancho a 320, 390, 760 y 1100 px.

Para validar lo pendiente: activar movimiento reducido y alto contraste del
sistema, probar zoom, lector de pantalla y sonido a volumen bajo; estas acciones
quedan descritas, no ejecutadas ni dadas por aprobadas.
