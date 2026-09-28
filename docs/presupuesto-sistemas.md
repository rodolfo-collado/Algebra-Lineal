# Presupuesto de entrada de Resolver un sistema

La política vive en `backend/presupuesto_sistemas.py`. Se aplica a la interfaz
web y a la aplicación desktop, que utiliza esas mismas vistas.

| Límite | Valor | Motivo |
| --- | ---: | --- |
| Ecuaciones | 12 | Acota las filas, las eliminaciones y el historial de pasos. |
| Variables | 12 | Acota pivotes, sustitución, expresiones y columnas del DOM. |
| Celdas aumentadas | 120 | Presupuesto conjunto: `ecuaciones × (variables + 1)`. Incluye b. |
| Texto del sistema | 10000 caracteres | Acota el análisis antes de separar ecuaciones; deja espacio para coeficientes, fracciones y formato educativo. |

Los tres límites estructurales se cumplen simultáneamente. Caben sistemas
cuadrados de hasta 10 variables, 12 ecuaciones con 9 variables, 10 con 11 y
9 con 12. Una matriz de 11 ecuaciones y 10 variables tiene **121 celdas** y se
rechaza aunque cada dimensión individual sea válida.

## Auditoría y protección

- **POST anterior:** `views.sistemas → form.is_valid → SistemaForm.clean`
  aceptaba enteros positivos sin máximo y construía el conjunto
  `nombres_esperados` con dos `range()`, antes de comprobar las celdas recibidas.
  Después construía filas, convertía números y llamaba al motor. La reconstrucción
  de valores tras un error también podía recorrer dimensiones arbitrarias.
- **GET anterior:** `inicial_desde` aceptaba cualquier entero positivo;
  `views.sistemas` lo pasaba a `valores_matriz_desde`, que reservaba listas sin
  necesitar un formulario validado ni una llamada al motor. `isdigit()` también
  admitía caracteres que `int()` no podía convertir.
- **Ahora:** los campos usan los máximos centrales; `clean()` comprueba el
  producto antes del primer `range()`. `inicial_desde` reutiliza la validación de
  los campos y descarta parejas fuera del presupuesto. La vista vuelve a
  comprobar la pareja y reconstruye GET solo en GET. Ambos helpers comprueban
  el presupuesto incluso si se invocan directamente; una entrada inválida
  devuelve `[]` sin leer celdas. El servicio también valida antes del motor.
- **Navegador:** `min/max` de los campos y `data-max-celdas` del fieldset salen
  de Python. `matriz.js` comprueba la estructura antes de leer/copiar celdas,
  `replaceChildren` o crear encabezados/nodos. Conserva la cuadrícula anterior
  ante dimensiones inválidas, muestra un aviso fuera del contenedor ocultable
  y bloquea el envío. Los botones respetan máximos individuales y presupuesto;
  las flechas navegan sobre las dimensiones de la cuadrícula conservada.
- **Texto:** no existía `max_length`; el límite general de cuerpo de Django no
  evitaba que una entrada corta como `x100000=1` reservara una fila enorme.
  Con `limitar_entrada=True`, el parser comprueba longitud antes de dividir,
  cantidad de ecuaciones antes de analizarlas y dimensiones antes de
  `[0] * cantidad_variables`. No cambia la gramática ni el algoritmo.
  `resolver_entrada_web` activa esa protección. El parser de consola conserva
  su contrato anterior por defecto; no recibe GET ni POST.

Se revisaron también `opciones_sistemas`, enlaces de exploración, rutas antiguas,
consumidores del parser en terminal, `backend/sistemas`, Gauss/Gauss-Jordan y
operaciones de fila. Los motores derivan dimensiones de matrices ya construidas;
no consumen directamente las dimensiones de HTTP. No se modificaron los
algoritmos, las opciones, la navegación ni la presentación del resultado.

## Costo observado

Mediciones locales orientativas en Windows/Python 3.13.3/Django 6.1.1, sin un
benchmark permanente: coeficientes densos pseudoaleatorios entre −5 y 5
(`Random(42)`), +30 en la diagonal, `b = suma(fila)`. Se ejecutaron ambos
métodos y el POST completo con todos los bloques. Los cuadrados de 12 se
midieron antes de activar la restricción.

| Ecuaciones × variables | Celdas | Motor + adaptación, ambos | POST completo | HTML |
| --- | ---: | ---: | ---: | ---: |
| 6 × 6 | 42 | 0,009 s | 0,49 s | 1,34 MiB |
| 8 × 8 | 72 | 0,025 s | 1,05 s | 3,70 MiB |
| 10 × 10 | 110 | 0,060 s | 2,46 s | 9,08 MiB |
| 12 × 12 | 156 | 0,115 s | 4,52 s | 18,30 MiB |
| 12 × 9 | 120 | 0,069 s | 2,85 s | 11,31 MiB |
| 10 × 11 | 120 | 0,061 s | 2,38 s | 10,26 MiB |
| 9 × 12 | 117 | 0,052 s | 1,95 s | 8,83 MiB |

Cada operación registra matrices antes/después; la presentación convierte todas
esas celdas y prepara Exacto/Decimal. En sistemas cuadrados densos, el número
de operaciones aritméticas crece aproximadamente como n³, mientras el volumen
de instantáneas puede crecer como n⁴. El tamaño de los racionales también
influye. Por eso no se reutiliza el presupuesto de 900 celdas de matrices.
Estas medidas justifican un techo educativo conservador, no una garantía de
tiempo o memoria para cualquier coeficiente o equipo.

## Campos reales de Django

El peor formulario normal de matriz envía **130 campos**:

- 120 celdas;
- 1 CSRF;
- 1 método, 1 tipo de entrada, 1 ecuaciones, 1 variables;
- 1 marcador `mostrar_definido`;
- 4 apariciones de `mostrar`, una por casilla.

El textarea está deshabilitado en modo matriz; los botones de estructura no
tienen `name`; Exacto/Decimal está fuera del formulario de entrada. Quedan
**870 campos de margen** frente a `DATA_UPLOAD_MAX_NUMBER_FIELDS=1000`.
No se modifica esa configuración.

La regresión obtiene los controles de la plantilla real, añade las 120 celdas
y envía tanto `application/x-www-form-urlencoded` como multipart con CSRF
habilitado, usando los motores reales. Cuenta las apariciones repetidas, no
solo las claves distintas, y exige que Django devuelva la solución.

## Cobertura y límites del incremento

`tests/test_presupuesto_sistemas.py` cubre límites individuales, 120/121 celdas,
POST y GET manipulados, reconstrucción directa y tras errores, entrada textual,
servicio directo y resolución densa en el máximo. Mocks que fallan en `range`
demuestran el rechazo previo, sin probar cargas gigantes. Las regresiones
existentes conservan clasificaciones, rectangulares, enlaces de exploración,
rutas antiguas, procedimiento plegable y Exacto/Decimal.

No hay un ejecutor DOM específico de Sistemas; la verificación interactiva usa
la página real sin instalar dependencias ni añadir infraestructura de navegador.

Pendiente fuera de este incremento: la longitud/magnitud de cada coeficiente
y los exponentes que admite `Fraction` siguen sin un presupuesto numérico
propio. Un límite de dimensiones o de caracteres no limita por sí solo el costo
de enteros o racionales de magnitud extrema. Tampoco se añade control de
concurrencia de peticiones ni se acotan aquí otros módulos matemáticos.
