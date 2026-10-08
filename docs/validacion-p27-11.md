# P27.11 — Claridad de entrada, cierre de P27 y PyGebra 0.9.0

7 de octubre de 2026, America/Managua. `git fetch origin develop` confirmó
`f2ed821c20c9365cffb746b31e147dea45c405b7`, merge de P27.10 (#79). Rama
`feature/p27-11-claridad-release-0.9.0`, creada desde ese SHA con el árbol limpio;
PR hacia `develop`. Es el último incremento de P27 y deja `develop` como candidato
de **PyGebra 0.9.0**. Sin merge, tag, GitHub Release ni refs manuales.

## Inspección y reproducción anterior al cambio

Se revisaron P27.8–P27.10, catálogo, layout, plantillas, `entradas.js`,
`vectores.js`, `matriz.js`, `conversion.js`, servicios y documentación. Cada punto
se reprodujo en @Browser con DOM/AX, medidas y POST reales. La skill
`frontend-testing-debugging` no está disponible en esta sesión; se usaron @Browser y
Chrome headless por CDP.

| Punto | Evidencia en la base |
| --- | --- |
| UI-07 | Inicio, Menú, migas y resultados del buscador decían «Álgebra Lineal». |
| UI-21 | Vectores, Bases numéricas y Numeración romana (una herramienta) nacían plegados como Matrices. |
| UI-40 | Una sola etiqueta («Número») y ayuda; `XIV` en Arábigo → romano daba «escrito solo con dígitos» y `14` en Romano → arábigo, ««1» no es un símbolo romano». |
| UI-41 | El número precedía a Base de origen: escribir `1A` con decimal por defecto mostraba «El dígito A no es válido en un número decimal.»; Tab: número → base. |
| UI-42 | Vectores `u, v, v3, v4`; ayudas «enteros o fracciones» en Vectores, Ax=b e Inversa y «números, enteros o fracciones» en la cuadrícula de Reducción; `0,5` → «'0,5' no es un número válido.»; resultado de Vectores con kicker igual al título. |
| UI-43 | «Sistema de ecuaciones» en el selector y en la etiqueta; 0 px entre la pista de Método/Entrada y el campo siguiente, en ambos modos. |
| UI-52 | Panel «Resultado final» en Reducción; Ax=b mezclaba `x₁` (ecuación matricial y vectorial) con `x1` (sistema equivalente, solución, justificación, interpretación). |
| UI-53 | «Las columnas resaltadas en la matriz final contienen un pivote.»: el bloque se llama Matriz escalonada/reducida y está en el procedimiento plegado. |
| UI-63 | «También puedes explorar…» en relacionadas y «También puedes explorar» en exploraciones, con reglas CSS duplicadas. |
| UI-72 | «Álgebra Lineal · Matrices» repetía las migas encima del h1 en las siete herramientas. |
| Pegado | `\n1\t2\n3\t4\n` → «Cada fila del bloque debe tener la misma cantidad de columnas.» |

## Cambios y decisiones

- **UI-07.** Solo cambia `catalogo.ALGEBRA_LINEAL`: Inicio, Menú, migas, buscador
  (contexto «Álgebra lineal · Matrices»), relaciones y anclas lo heredan. Se
  conservan `AlgebraLineal.exe`, el repositorio, rutas, clases, `verbose_name` y los
  accesos históricos «Álgebra Lineal.lnk» que el instalador retira.
- **UI-21.** `Categoria.herramienta_unica` (exactamente una herramienta disponible)
  añade `open` al tema en `pages/_area.html`, sin nombres fijos: hoy Vectores,
  Bases numéricas y Numeración romana. Las áreas siguen plegadas, Matrices también;
  no se guarda nada y el filtro en vivo restaura lo que el usuario abrió o cerró
  (verificado cerrando Vectores y abriendo Matrices antes de filtrar).
- **UI-40.** Etiqueta y ayuda tienen un `span[data-direccion]` por dirección; una
  regla CSS `:has` muestra la de la dirección marcada, también sin JavaScript (no
  había placeholder). `servicios_romanos.sugerir_direccion` intenta la conversión
  opuesta con el parser real: solo si tiene éxito el error dice «XIV parece un número
  romano. Cambia a Romano → arábigo.» o «14 está escrito con cifras arábigas. Cambia a
  Arábigo → romano.». Si no vale en ninguna dirección (`IIII`, `0`, `4000`, `abc`)
  queda el error original. No cambian algoritmo, rangos ni formas aceptadas, y nada
  se convierte por su cuenta.
- **UI-41.** Base de origen → número → «Convertir a». Se retira el contenedor
  `.base-selectors` que agrupaba origen y destinos; etiqueta, perfil del teclado,
  validación en vivo, Enter, memoria POST y fallback sin JS no cambian
  (`conversion.js` intacto). Tab real: migas → base → número → destinos → Convertir.
- **UI-42.1.** `v1, v2, …, vn` en suma, resta y operandos múltiples, y también en la
  multiplicación por escalar (`k·v1`): un solo convenio y la misma memoria por nombre
  al cambiar de operación (antes Suma y Escalar compartían `u`). Agregar no renombra.
  Combinación lineal conserva `v1 … vk`, `b` y sus incógnitas. Backend: los mensajes
  de dimensión usan los nombres de la interfaz.
- **UI-42.2.** «Escribe enteros, fracciones como 1/2 o decimales con punto, como
  0.5» en Vectores, Ax=b e Inversa; la cuadrícula de Reducción (plantilla y
  `matriz.js`) dice «enteros, fracciones o decimales con punto». Operaciones y el
  campo de texto de Reducción ya lo decían.
- **UI-42.3.** En `convertir_a_numero`, el punto común de celdas y componentes: un
  texto con una sola coma entre cifras, sin espacios (`0,5`, `-3,14`, `,5`), añade
  «Usa punto para los decimales, por ejemplo 0.5.». `1,000` (posible separador de
  miles), listas (`1,2,3`, `1, 2`) y texto no reciben sugerencia. Sin conversión ni
  cambio de gramática.
- **UI-42.4.** UI-72 no lo resolvía: la repetición estaba en el encabezado del
  resultado de Vectores (kicker = operación, h2 = título). Se aplica el mismo
  criterio: se retira ese kicker y el dato `etiqueta`, que quedó sin uso.
- **UI-43.** El campo de texto se llama «Ecuaciones»; la opción sigue siendo
  «Sistema de ecuaciones» y la leyenda oculta del fieldset también. `.choice-row`
  recupera `margin-bottom: 1rem`, la separación normal de `.choice-fieldset`, en
  sistema y en matriz aumentada.
- **UI-52.1.** «Resultado» en Reducción, como en las demás herramientas. Sin
  procedimiento ni comparación ya no se muestra el kicker «Resultado», que habría
  repetido el panel.
- **UI-52.2.** Filtro de plantilla `incognitas` (`templatetags/numeros.py`): `x1`
  → `x₁` en resultados y procedimientos de Reducción, Ax=b y Combinación lineal.
  Servicios, backend, terminal, parser, campos, placeholders, ayudas y teclado siguen
  en `x1`. Operaciones con matrices conserva su notación lineal ASCII
  (`x1 a1 + x2 a2`, `[3, 1, 0]^T`), coherente en sí misma: subir solo `x` crearía
  una mezcla nueva.
- **UI-53.** «Los pivotes se resaltan en la matriz escalonada | reducida | escalonada
  y en la matriz reducida» según el método, más «del procedimiento» cuando la matriz
  está dentro del desplegable (también en Ax=b).
- **UI-63.** `related_tools.html` reutiliza `.explore`/`.explore-title` y dice
  «También puedes explorar». Se borran las reglas `.related` y `.related-title`; las
  listas, destinos, relaciones y pruebas de Romanos (`related-link`) no cambian.
- **UI-72.** El layout común deja migas → h1 → descripción y se borra el CSS de
  `.tool-kicker`. Los kickers de resultados que aportan método, dimensiones o
  contexto se conservan.
- **Pegado (bug de P27.9).** `entradas.js` descarta las líneas vacías del inicio y
  del final antes de construir el bloque. Una fila vacía interior sigue siendo una
  fila y se valida igual (todo o nada). Un valor rodeado de saltos conserva el paste
  nativo.

## Contrato x1 / x₁

| Contexto | Escritura |
| --- | --- |
| Campos, placeholders, ayudas de sintaxis, cuadrícula de entrada e inserción del teclado | `x1, x2, …` |
| Resultado y procedimiento de Reducción, Ax = b y Combinación lineal | `x₁, x₂, …` |
| Operaciones con matrices (vectores lineales y determinación) | `x1 a1`, ASCII coherente, sin cambios |
| Servicios, backend y terminal | `x1, x2, …` |

## Regresiones con capturas congeladas

Las capturas de P26.3 (`_regresion_sistemas_bloques_base.py`) y P26.4
(`fixtures/reduccion_filas_p264.json`) no se regeneran desde el código nuevo.
`tests.ayudas.antes_de_p2711` deshace en el HTML solo los tres cambios deliberados
(título del panel, leyenda y `x₁`); el resto de la salida sigue igual byte a byte
a esas capturas, y los datos de los servicios no cambian.

## PyGebra 0.9.0

### Qué representa

MINOR (0.8.0 → 0.9.0): P27 amplía la experiencia de forma compatible y no cambia la
matemática ni los contratos de cálculo. En términos de usuario:

- **Identidad PyGebra consolidada** en la aplicación, el instalador, los accesos y
  Configuración de Windows, conservando AppId, AUMID y carpeta.
- **Teclado matemático contextual**: aparece en el campo enfocado con las teclas que
  ese campo acepta.
- **Entradas más seguras y sin pérdida**: cambiar dimensiones, operación o modo no
  borra lo escrito; las entradas inválidas se explican.
- **Feedback, errores y cálculos largos**: errores junto al campo y con foco, espera
  visible y confirmación antes de cálculos pesados.
- **Buscador y orientación**: filtro en vivo, verbos de acción y relaciones entre
  herramientas.
- **Resultados y procedimientos más claros**: procedimiento plegable, un solo
  resultado, aviso de resultado desactualizado y notación coherente.
- **Mejoras de escritorio**: Alt+←/→, menú contextual de edición y páginas de error
  propias.
- **Preferencias persistentes** de tema, formato Exacto/Decimal y precisión.
- **Accesibilidad y responsive**: foco visible, contraste, alto contraste y
  pantallas estrechas.
- **Copiar y pegar** bloques de matrices y vectores desde hojas de cálculo o
  resultados.
- **Navegación y edición de celdas** con flechas sin perder la edición de texto.
- **Claridad final de formularios** (este incremento).

No incluye P28 (selección matricial) ni actualizador.

### Archivos de versión

| Archivo | Cambio |
| --- | --- |
| `pyproject.toml` | `version = "0.8.0"` → `"0.9.0"`. |
| `uv.lock` | Regenerado con `uv lock`: solo el paquete raíz `algebra-lineal` 0.8.0 → 0.9.0; 30 paquetes, sin dependencias nuevas. |
| `docs/releases.md` | La frase de la versión preparada describe 0.8.0 → 0.9.0. |
| `tests/test_release.py` | La versión preparada coincide con `uv.lock` y no retrocede de 0.9.0, sin fijar el número exacto. |

Referencias restantes, revisadas una por una (sin reemplazo global):

| Referencia | Decisión |
| --- | --- |
| `release.yml` y `docs/releases.md`: `0.10.0 > 0.9.0` | Ejemplo de comparación numérica; se conserva. |
| `docs/identidad-visual.md` y `docs/instalacion-windows.md`: «Actualizar desde 0.8.0», `AlgebraLineal-Setup-0.8.0.exe` | Migración desde la release publicada, vigente para 0.9.0; se conserva. |
| `scripts/test_windows_distribution.ps1`: base 0.8.0 | Prueba de actualización desde la release publicada; se conserva. |
| `tests/test_release.py`, `tests/test_instalador.py` | Fixtures de versiones y repositorios temporales; se conservan. |
| `docs/validacion-p27-2.md` | Informe histórico; no se reescribe. |

`README.md` usa el badge dinámico de la última release y no fija la versión.

### Candidato de release

`git fetch origin --tags`: `v0.9.0` no existe en el remoto ni localmente; la última
estable es `v0.8.0`.

```text
$ uv run --locked python scripts/validate_release.py --ref refs/heads/main --sha "$(git rev-parse HEAD)"
Candidato validado: v0.9.0 en c3fa99aec95830fc52a4d1464ccff9f6425c3d61
```

Se ejecutó sobre el commit de versión. El hash de `git for-each-ref` fue idéntico
antes y después: no se crearon tags ni se movieron refs. El commit de documentación
posterior no cambia `pyproject.toml`; Release volverá a validar el SHA real del push
a `main`. El workflow no cambia: deriva `v0.9.0`, espera
`PyGebra-Setup-0.9.0.exe`, genera `SHA256SUMS.txt` y publica tras CI, build y smoke.

### Build Windows

`.\scripts\build_windows.ps1` (PyInstaller + Inno Setup 6, flujo existente):
«Distribución lista (22.1 MiB)».

| Dato | Valor |
| --- | --- |
| Instalador | `dist\installer\PyGebra-Setup-0.9.0.exe` (único archivo de la carpeta) |
| Tamaño | 23 145 234 bytes |
| SHA-256 | `1e08c0d56a938923e083d75fc466e9b1d6c91dfe3089f9dc32202ba66037a181` |
| EXE | ProductName/FileDescription PyGebra, CompanyName Proyecto PyGebra, OriginalFilename `AlgebraLineal.exe`, FileVersion y ProductVersion 0.9.0 |
| Instalador (VersionInfo) | ProductName PyGebra, ProductVersion 0.9.0, CompanyName Proyecto PyGebra |

`AlgebraLineal.exe` sigue siendo el nombre técnico deliberado.

### Instalación, aperturas y actualización desde 0.8.0

La cuenta habitual conserva accesos de una instalación anterior, así que, como en
P27.2, se usó **Windows Sandbox** (usuario `WDAGUtilityAccount`, PowerShell
5.1.26100.9549) con el smoke existente sin cambios de lógica. Base: el instalador
**publicado** `AlgebraLineal-Setup-0.8.0.exe`, SHA-256
`6bba9c42b1ebfebdc0439951704f80a245339bc9fddf97aeea665ab867e37263`, igual al
`SHA256SUMS.txt` de la release. **Resultado: PASS** en las tres pasadas.

| Pasada | Resultado |
| --- | --- |
| Instalación limpia | Identidad PyGebra / Proyecto PyGebra, EXE 0.9.0, AUMID `PyGebra.Desktop`, sin accesos históricos; dos aperturas (Django/Waitress, Gauss y Gauss-Jordan, Operaciones, productos, Ax = b con `x₁ = 2`, recursos y cierre); desinstalación limpia. |
| 0.8.0 con acceso de escritorio → 0.9.0 | Base verificada (Álgebra Lineal, mismo AppId y AUMID); el candidato, sin `/DIR`, conserva la carpeta; accesos PyGebra y ningún histórico; dos aperturas; desinstalación. |
| 0.8.0 sin acceso de escritorio → 0.9.0 | Igual, sin acceso opcional. |
| Preferencias | `preferencias.json` válido (oscuro, Decimal, 6) con el mismo SHA-256 tras ambas actualizaciones y desinstalaciones. |

Logs locales, ignorados por Git: `build/p27-11/sandbox-output/`.

## Pruebas automáticas

| Comando | Resultado |
| --- | --- |
| `uv run --locked python --version` | Python 3.13.3 |
| `uv run --locked python -m unittest discover -v` | 1631 OK, 1 omitida, 120.9 s |
| `uv run --locked python manage.py check` | Sin problemas, 0 silenciados |
| `uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py` | OK |
| `uv lock --check` | OK, 30 paquetes |
| `git diff --check` | OK |
| `node --check` | Todos los scripts de `static/calculadora` y los runners, OK |
| Versión en `pyproject.toml` | `0.9.0` |

Nuevas: `tests/test_claridad_p2711.py` (15 pruebas) y la prueba de versión
preparada en `test_release`. Se actualizaron las pruebas que fijaban el contrato
anterior (`u/v`, «Resultado final», `x1` en la salida, kicker, «Álgebra Lineal»,
temas plegados, mensajes de Romanos); los datos de entrada siguen escribiéndose `x1`.

## Runners DOM

| Runner | Resultado |
| --- | --- |
| `claridad_browser` (P27.11, nuevo) | 30/30 |
| `entrada_edicion_browser` (P27.9 + 6 casos de P27.11) | 39/39 |
| `residual_browser` (P27.10) | 39/39 |
| `pulido_browser` (P27.8) | 16/16 |
| `resultado_browser` (P27.6) | 66/66 |
| `escritorio_browser` (P27.7) | 27/27 |
| `buscador_browser` (P27.5) | 16/16 |
| `feedback_browser` (P27.4) | 19/19 |
| `teclado_browser` (P27.3) | 30/30 |
| `entradas_browser` (P27.1) | 19/19 |
| `operandos_browser` | 15/15 |
| `inversa_browser` | 7/7 |
| `presentacion_browser` | 14/14 |
| **Total** | **337/337** |

`claridad_browser` pasó 30/30 también en @Browser. Con el panel de Browser oculto la
página no tiene foco y los casos que abren el teclado con `focus()` no pueden pasar
(un caso de P27.9 lo mostró); por eso la tabla corresponde a Chrome headless por CDP
con emulación de foco y un perfil limpio por runner, sin dependencias nuevas.

## QA en @Browser y matriz responsive

@Browser, con la app real y POST reales: Inicio (temas abiertos, Matrices plegado,
filtro que restaura el estado manual); las siete herramientas sin kicker; Reducción
(«Ecuaciones», 16 px tras las pistas en ambos modos, Gauss con `x₁`, leyenda y
«Resultado»); Ax = b sin `x1` en el resultado; Vectores (`v1…v4`, quitar con estado
y foco, memoria al pasar a Escalar y Combinación, dimensión 10, `0,5` y `1,000`);
Romanos (cambio de etiqueta y ayuda, `XIV` escrito y enviado con clic, doce casos de
sugerencia); Bases (Hexadecimal elegido, `1A` escrito sin aviso, teclado A–F, Tab
real base → número → destinos → Convertir, `1A₁₆ = 11010₂`); pegado sobre la página
real (exteriores, interior y valor único).

Chrome headless por CDP: 1280×650, 760×560 y 390×650 en claro y oscuro sobre
Inicio, Reducción (formulario y resultado), Bases, Romanos con error, Vectores, Ax =
b con resultado e Inversa, y forced-colors emulado en claro y oscuro sobre Inicio,
Reducción, Bases y Romanos: **72 combinaciones, 0 problemas** (sin desborde de
página, cabecera visible, sin kicker y controles dentro del ancho). Se revisaron las
capturas de Bases y Vectores a 390 px oscuro, Romanos a 390 px claro, Reducción a
390 px oscuro con forced-colors, Inicio a 390 px claro y Ax = b a 1280 px claro.
En forced-colors se conservan la identidad del header (logo y nombre en
`CanvasText`), los bordes de Menú/Tema, los radios segmentados y las migas.

## Archivos modificados

74 archivos respecto de `f2ed821`. Implementación (31): `backend/parser_sistemas.py`, `backend/vectores.py`,
`frontend/web/calculadora/{catalogo,forms,opciones_vectores,servicios_romanos,servicios_vectores}.py`,
`frontend/web/calculadora/templatetags/numeros.py`,
`static/calculadora/{entradas,matriz,vectores}.js`,
`static/calculadora/styles/{components,modules}.css`, las plantillas
`components/{related_tools,vector}.html`, `layouts/herramienta.html`,
`pages/_area.html`, `modules/bases/index.html`,
`modules/ecuaciones/{_equivalencias,_metodos,index}.html`,
`modules/inversa/index.html`, `modules/romanos/index.html`,
`modules/sistemas/{_bloques_metodo,_pivotes,_solucion,index}.html`,
`modules/vectores/{_combinacion,_fila,index}.html` y
`scripts/test_windows_distribution.ps1`.

Pruebas (32): `tests/ayudas.py`, `tests/claridad_browser.{py,js}` (nuevos),
`tests/test_claridad_p2711.py` (nuevo), los runners
`entrada_edicion`, `entradas`, `feedback`, `operandos`, `pulido`, `residual` y
`resultado` (`.js`, y `.py` en este último), y `test_desktop`, `test_ecuaciones_matriciales_web`,
`test_entradas_seguras`, `test_feedback`, `test_interfaz_progresiva`,
`test_navegacion`, `test_numeros_romanos_web`, `test_operandos_multiples`,
`test_presentacion_numerica`, `test_presupuesto_computacional`,
`test_presupuesto_sistemas`, `test_procedimiento_plegable`, `test_reduccion_filas`,
`test_regresion_sistemas_bloques`, `test_release`, `test_resolver_sistema`,
`test_seguridad_numerica`, `test_teclado`, `test_vectores_web` y `test_web`.

Versión (2): `pyproject.toml`, `uv.lock`.

Documentación (9): `docs/validacion-p27-11.md` (nuevo), `docs/interfaz.md`,
`docs/funcionalidades.md`, `docs/pruebas.md`, `docs/releases.md`,
`docs/identidad-visual.md`, `docs/arquitectura.md`, `docs/matriz-inversa.md` y
`docs/presupuesto-sistemas.md`. Los informes P27.1–P27.10 no se modifican.

## Commits

1. `131f0e4` — feat: cerrar claridad de entrada y notación P27.11 (código y pruebas).
2. `c3fa99a` — chore: preparar PyGebra 0.9.0 (versión, lockfile, `releases.md` y
   prueba de versión).
3. docs: contratos de interfaz y esta validación.

## Límites

- La publicación real ocurre solo tras el merge a `main`, con CI, build, smoke, tag
  y release automáticos; aquí no se creó ni se probó un tag remoto.
- No se inspeccionaron a mano Inicio de Windows, la búsqueda, `shell:AppsFolder`, el
  asistente ni Configuración; el smoke comprueba registro, accesos, metadatos y dos
  aperturas.
- El pegado se probó con el evento `paste` real del navegador y `DataTransfer`, sin
  tocar el portapapeles del sistema de la cuenta; Ctrl+V real ya se validó en P27.9 y
  usa el mismo manejador.
- forced-colors se emuló en Chromium; no se usó un tema de contraste físico ni un
  lector de pantalla.
- Operaciones con matrices mantiene su notación lineal ASCII por decisión; unificarla
  exigiría rediseñar también `a1` y `^T`.
- Capturas, logs y scripts de QA quedan fuera del repositorio (scratchpad y
  `build/p27-11/`).
