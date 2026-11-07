# Conjuntos: definición, relaciones y operaciones finitas

[Índice](README.md) · Herramienta web y desktop: **Conjuntos → Conjuntos finitos → Relaciones entre conjuntos**.

P1 está completado e integrado mediante el [PR #104](https://github.com/rodolfo-collado/Algebra-Lineal/pull/104).
P2–P6 extienden el mismo parser y evaluador con operaciones finitas, generación, intervalos, Venn y cardinalidades. Todo el trabajo continúa en la rama `feature/conjuntos-p2-operaciones` y el PR #113.
El acceso público está temporalmente bloqueado: Conjuntos figura como
**Próximamente**, igual que Cálculo, y las URL `/conjuntos/…` responden 404.
La implementación, los avances y la documentación que sigue se conservan.
Las pruebas matemáticas siguen activas; las del editor usan una URLConf exclusiva
de pruebas, que no habilita el módulo en la aplicación ni en el ejecutable.
Consulta el [TODO de Conjuntos](TODO-conjuntos.md) para el estado de P1–P7, las mejoras
detectadas en las pruebas desktop y las posibles extensiones futuras.

## Definir y editar

En **Nueva definición**, escribe `A = {1, 2, {3, 4}, "rojo"}` y pulsa
**Añadir conjunto**. Cada definición tiene nombre y contenido editables por
separado. **Guardar cambios** aplica la edición sin calcular; **Calcular expresión**
también usa las definiciones editadas. Eliminar quita solo la definición elegida:
si una expresión aún la referencia, el próximo cálculo explica que falta.
Los conjuntos pertenecen al formulario actual, como los operandos de matrices;
no se guardan en disco ni entre aperturas de la herramienta.

Los nombres cumplen `[A-Za-z][A-Za-z0-9_]*`, son únicos y distinguen mayúsculas.
Ejemplos: `A`, `S`, `Conjunto1`, `Grupo_2`. No se admiten palabras de Python,
`true`, `false`, `none`, `in`, `not`, `union`, `interseccion`, `diferencia`,
`potencia`, `par`, `intervalo` o `vacio` (sin distinguir mayúsculas para la reserva).
Al renombrar se sustituyen referencias completas en la expresión, simultáneamente;
renombrar `A` no cambia `AA` ni el texto `"A"`.

## Literales y tipos

- `{}` y `∅` son el mismo conjunto vacío.
- Números exactos: enteros con signo, fracciones `-1/2`, decimales `0.5` o `.5`.
  Se reutilizan `convertir_a_numero` y la protección numérica común. No hay
  notación científica, coma decimal, separadores de miles ni cálculos numéricos.
- Texto con comillas dobles y escapes JSON: `"rojo"`, `"a,b"`, `"una \"cita\""`.
  No se convierte texto a número: `1` y `"1"` son elementos distintos.
- Conjuntos anidados: `{1, {1}, {{1}}}` tiene tres elementos distintos.
  No se aplanan los conjuntos interiores y no necesitan nombre.
- El orden no importa y los duplicados se normalizan recursivamente:
  `{1, 1.0, 2/2}` es `{1}`. La presentación canónica no promete orden numérico.

Los literales contienen **datos**, no referencias: `{A}` es inválido; usa
`{{1, 2}}` para contener un conjunto o `{"A"}` para contener ese texto.
Así no existen referencias cíclicas ni dependencias ocultas entre definiciones.

## Operaciones, relaciones y agrupación

La expresión puede producir un conjunto, un número, un texto o un booleano.
Un operando es un nombre definido, un número, un texto, un conjunto, un par, una región real o una operación.
Los paréntesis agrupan valores: `((A)) ⊆ ({1, 2})` y `(A ∪ B) ∩ C`.
Se admite como máximo una relación, en el nivel exterior; no se admiten relaciones
encadenadas ni agrupadas como valores, ni operadores ASCII alternativos.
`A = {1}` en el editor define A; en **Expresión** compara A
con `{1}` y nunca modifica su definición.

| Operación | Sintaxis | Regla |
| --- | --- | --- |
| Unión | `A ∪ B` | Elementos que pertenecen al menos a uno de los conjuntos. |
| Intersección | `A ∩ B` | Elementos que pertenecen a ambos conjuntos. |
| Diferencia | `A ∖ B` | Elementos de A que no pertenecen a B. El orden importa. |
| Complemento | `∁(A, U)` | Exige A ⊆ U y devuelve los elementos de U que no pertenecen a A. |
| Cardinalidad | `|A|` | Cuenta los elementos distintos completos; devuelve un `Fraction` entero. |

En P2 las operaciones exigen conjuntos finitos; P4 extiende unión, intersección,
diferencia y complemento a regiones reales. El universo del complemento es
un segundo argumento obligatorio y puede ser una expresión: `∁(A, A ∪ B)`.
No se infiere un universo de otros conjuntos definidos y se rechaza A si contiene
algún elemento ajeno a U. No hay complemento unario ni función con nombre reservado.
La diferencia utiliza **U+2216 `∖`**, no barra inversa ni el signo de resta.

Precedencia, de mayor a menor: agrupaciones, funciones y `|…|`; producto `×`;
intersección `∩`; después `∪` y `∖`, con igual prioridad y asociación a la izquierda; al final la
relación opcional. Así `A ∪ B ∩ C` significa `A ∪ (B ∩ C)` y `A ∖ B ∪ C`
significa `(A ∖ B) ∪ C`. Usa `A ∖ (B ∪ C)` si quieres excluir ambos.
La cardinalidad produce un número, por lo que `|A| ∪ B` se rechaza por tipos.
Los conjuntos anidados siguen siendo elementos completos: `|{1, {1}, {{1}}}| = 3`.
Las definiciones admiten conjuntos finitos o un intervalo literal; `S = A ∪ B` no define S.

| Relación | Regla |
| --- | --- |
| `x ∈ A` | x coincide con un elemento completo de A. |
| `x ∉ A` | x no coincide con ningún elemento de A. |
| `A ⊆ B` | Cada elemento de A pertenece a B. |
| `A ⊂ B` | A está incluido en B y ambos son distintos. |
| `A = B`, `A ≠ B` | Igualdad o desigualdad extensional, sin orden ni duplicados. |

Pertenencia exige un conjunto a la derecha; inclusión exige dos conjuntos.
Igualdad y desigualdad exigen tipos compatibles: dos conjuntos, dos números o
dos textos. El vacío está incluido en cualquier conjunto, pero solo pertenece
a los que lo contienen como elemento: `∅ ∈ {∅}`.

**Construir con ayuda** propone nombres mediante los controles nativos de
autocompletado y permite escribir literales. **Usar expresión** genera texto
editable: no ejecuta otro cálculo. También funciona mediante POST sin JavaScript.
El teclado contextual reutiliza el dock existente, con nombres de conjuntos,
llaves, comillas, separador, relaciones y operaciones finitas. El resultado es un
único conjunto, número, texto, **Verdadero** o **Falso**, acompañado de un
procedimiento inicialmente plegado. Por ejemplo, `|A ∩ B| ∈ {0, 1, 2}` evalúa
primero la operación y después la pertenencia.

## Capas y protección

- `backend/conjuntos/modelo.py`: `Conjunto` inmutable sobre `frozenset`, números
  `Fraction` y textos. Igualdad y pertenencia usan valores, no el texto escrito.
- `literales.py`: lector de datos y definición `nombre = literal`.
- `parser.py`: árbol `Operacion` / `Relacion` / `Referencia`, agrupación y renombrado por tokens.
- `evaluador.py`: valores exactos y evidencia didáctica, independiente de Django.
- `presupuesto.py`: consumo acumulado antes de construir conjuntos. Comparte
  `LONGITUD_SISTEMA_MAXIMA` (10 000 caracteres), `CELDAS_MAXIMAS` (900 nodos de
  valores, incluidos contenedores y duplicados) y `OPERANDOS_MAXIMOS` (50 conjuntos
  definidos; hasta 50 niveles de lectura contando operandos y agrupaciones).
  La longitud se suma entre nombres, contenidos y expresión. Un POST no obtiene
  un presupuesto nuevo por cada definición. No son límites matemáticos nuevos.
- El mismo `Presupuesto` acompaña lectura y evaluación. P2 reserva acumuladamente
  hasta `CELDAS_MAXIMAS * OPERANDOS_MAXIMOS` (45 000) unidades de cálculo y otras
  45 000 de procedimiento, antes de construir cada resultado o formatearlo.
  Se cuenta el peso recursivo de los valores (incluidos conjuntos interiores),
  dos recorridos por operación y los operandos y el resultado potencial en cada
  paso. Son unidades de recorrido y volumen, no comparaciones de bits ni segundos.
  Las cadenas asociadas a la izquierda también tienen un máximo de 50 niveles
  de AST. Esto impide multiplicar trabajo y evidencia reutilizando referencias
  pequeñas en el texto. Las relaciones aisladas de P1 conservan sus entradas válidas.
- Formularios, vista y servicio web: contrato HTTP estricto, errores vinculados
  a los campos, evaluación única y adaptación al componente `disclosure`.
  El catálogo sigue siendo la única fuente de navegación y búsqueda.

Se rechazan entradas excesivas, cierres incorrectos, nombres desconocidos,
campos repetidos/ajenos y sintaxis de código. No se utiliza ejecución de Python,
`eval` ni bibliotecas externas de álgebra. Los textos se presentan con escape HTML.
La evidencia añade un paso por operación y uno por relación, en orden de evaluación;
no genera un paso por combinación de elementos. `Resultado.estimacion` reutiliza el contrato `Estimacion` del
presupuesto computacional, con trabajo de comparación y presentación separados;
no es una predicción de segundos calibrada para conjuntos.

## Contrato para presentación (Claude)

`analizar_expresion(texto, presupuesto=…)` devuelve el mismo AST extendido:
`Operacion(operador, operandos)` es inmutable y produce un valor.
`analizar_relacion` y `evaluar_relacion` conservan la exigencia de una relación;
`evaluar_expresion(arbol, entorno, presupuesto=…)` admite ambos casos.
No se modifica el entorno y cada subexpresión se evalúa una sola vez.

`Resultado` conserva `valor`, `pasos` (texto listo para mostrar) y `estimacion`,
y añade `procedimiento: tuple[Paso, …]`. Cada `Paso` inmutable expone:

- `operador`, `operandos` (valores matemáticos ya resueltos), `resultado` y `regla`.
- `explicacion`, lista para mostrar; no es un formato que el frontend deba analizar.
- `testigo`: elemento que incumple una inclusión, o `None`.
- `pertenece`, `incluido`, `iguales`: hechos booleanos calculados por el motor,
  o `None` cuando no aplican. `∁` entrega `incluido=True` tras validar el universo.

Las reglas son `union`, `interseccion`, `diferencia`, `complemento`, `cardinalidad`,
`pertenencia`, `inclusion`, `inclusion_propia`, `igualdad` y `desigualdad`.
`∉` usa `pertenencia` y conserva en `pertenece` el hecho positivo; el veredicto de
la negación vive en `resultado`. `⊂` conserva por separado `incluido` e `iguales`.

El servicio web mantiene las claves de P1 (`expresion`, `respuesta`, `pasos`,
`estimacion`) y añade `datos`. La plantilla lo entrega mediante `json_script`
en `#conjuntos-resultado-datos`, incluso sin JavaScript. `datos` tiene `valor`
y `procedimiento`, con los mismos campos anteriores y los valores serializados:

```json
{"tipo": "numero", "numerador": "1", "denominador": "2"}
{"tipo": "texto", "valor": "1"}
{"tipo": "conjunto", "elementos": []}
{"tipo": "booleano", "valor": true}
```

Los números usan cadenas para evitar pérdida de precisión en JavaScript.
`elementos` contiene valores tipados recursivos en orden canónico de presentación;
no promete orden numérico. Claude puede presentar cada paso desde sus operandos,
resultado, regla y hechos, sin interpretar `respuesta`/`explicacion`, reconstruir
conjuntos desde texto ni calcular de nuevo operaciones o relaciones.
El editor y el teclado existentes permiten probar P2–P6 con la URLConf de pruebas;
el refinamiento visual, Estudio y Minimalista quedan fuera de este incremento.

## Potencia, producto cartesiano y pares (P3)

`potencia(A)` genera todos los subconjuntos, incluido el vacío. `A × B` genera
pares `par(a, b)`, distintos de los conjuntos de dos elementos. Las posiciones
importan: `par(1,2) ≠ par(2,1)`. Pueden contener valores anidados y aparecer dentro
de literales: `{par(1,{2})}`. Los literales siguen sin admitir referencias.
`par(A,B)` en una expresión sí resuelve ambas referencias con el mismo evaluador.
El producto tiene mayor prioridad que ∩ y se asocia a la izquierda:
`A × B × C` contiene pares `par(par(a,b),c)`, no ternas implícitas.

La generación es manual. Antes de enumerar se reserva el peso recursivo del
resultado expandido (2^n subconjuntos o n×m pares), los operandos y su presentación.
Las solicitudes que exceden el presupuesto acumulado se rechazan antes de crear
los resultados. No se truncan resultados ni se sustituyen por aproximaciones.

## Intervalos y recta real (P4)

La sintaxis literal es `intervalo(inferior, superior, abierto, cerrado)`; ambos
cierres admiten `abierto` o `cerrado`. Ejemplos:

- `intervalo(0,1,abierto,abierto)` representa (0,1).
- `intervalo(0,1,cerrado,cerrado)` representa [0,1].
- `intervalo(-inf,2,abierto,cerrado)` representa (−∞,2].
- `intervalo(0,inf,cerrado,abierto)` representa [0,+∞).

También se aceptan −∞ escrito como `-∞` y +∞ como `∞` o `+∞`.
Los infinitos no son elementos ni extremos cerrados. Un inferior mayor que el
superior es inválido; extremos iguales solo producen un punto si ambos son
cerrados, y en los demás casos producen el vacío.

`Recta` es una tupla inmutable y canónica de `Intervalo`: admite resultados
disjuntos. Unión, intersección, diferencia y complemento explícito conservan las
fronteras exactas y los huecos. Dos tramos contiguos solo se fusionan si incluyen
el punto de contacto. También admite pertenencia numérica, inclusión e igualdad.
El vacío finito ∅ es compatible con la región real vacía. Las operaciones mixtas
entre conjuntos finitos **no vacíos** y regiones reales se rechazan explícitamente.
La cardinalidad de un intervalo no degenerado es infinita: `|…|` informa que no
existe cardinalidad finita; las uniones de puntos cerrados sí se pueden contar.

La salida JSON usa `tipo: "recta"`, con `intervalos` y extremos numéricos tipados
(o null para el infinito correspondiente), y los dos indicadores de cierre.
`datos.recta` aporta `tramos` con posiciones acotadas, etiquetas exactas, cierres,
`punto`, `pertenece` y `x_punto`. Solo las posiciones de dibujo son aproximadas;
las operaciones y la consulta del punto son racionales exactas. La interfaz ofrece
zoom, desplazamiento, restablecer, selección de tramo y consulta exacta por POST.
Sin JavaScript se conservan el resultado textual y la consulta de pertenencia.

## Diagramas de Venn (P5)

En «Recta real y diagramas de Venn», indica `A, B` o `A, B, C`, opcionalmente
el nombre de un universo definido, y calcula por ejemplo `(A ∪ B) ∖ C`.
El universo explícito debe contener todos los conjuntos. Sin universo se conoce
la unión, pero la región exterior se marca como desconocida.

Cada elemento completo, incluidos conjuntos anidados y pares, se distribuye en
una única región. El backend selecciona también regiones vacías usando el mismo
AST y evaluador sobre marcadores de región: el frontend no repite operaciones.
El selector admite nombres elegidos, ∅, ∪, ∩, ∖ y ∁; rechaza generación,
cardinalidades, relaciones y literales no vacíos porque no representan regiones
completas del diagrama elegido.

`datos.venn` contiene `nombres` y 4 u 8 `regiones`. Cada región incluye `mascara`,
`pertenece` (booleanos en orden de nombres), `elementos` tipados, `etiquetas` listas
para mostrar, `cantidad` exacta como cadena (null si el exterior es desconocido),
`seleccionada` y `exterior_conocido`. El bit 0 representa A, el 1 B y el 2 C;
la máscara 0 es el exterior. El SVG usa recortes de círculos para resaltar las
regiones correctas; botones accesibles muestran sus detalles. La tabla funciona
sin JavaScript y evita depender exclusivamente del color.

## Cardinalidades e inclusión-exclusión (P6)

El enlace «Cardinalidades e inclusión-exclusión» abre el formulario de dos o tres
conjuntos. Permite editar regiones exclusivas o cardinalidades inclusivas de
A, B, C y sus intersecciones. Al cambiar número o modo se ajustan los campos;
sin JavaScript pulsa «Aplicar número y tipo de datos». Indica todos los ceros.
El universo es opcional, pero obligatorio para expresiones con complemento.

La inversión de intersecciones resta primero las regiones superiores ya
calculadas, de la triple hacia las simples. Cualquier región negativa denuncia
datos incoherentes. La unión se verifica con inclusión-exclusión: simples menos
dobles más triple. El universo no puede ser menor que la unión. Solo se aceptan
enteros no negativos de hasta 100 cifras, sin pérdidas de precisión.

`resolver_cardinalidades` devuelve regiones exclusivas, intersecciones inclusivas,
unión, regiones seleccionadas, resultado y pasos estructurados. Las reglas son
`region_exclusiva` (valor inicial, sustraendos identificados y resultado),
`inclusion_exclusion` (términos con máscara, signo y valor) y `suma_regiones`.
El JSON de esta pantalla comparte `venn` y entrega `resultado`, `union` y `pasos`;
las cantidades son cadenas exactas, las máscaras y signos son enteros pequeños.
El exterior desconocido queda como null. Nunca se infiere un universo numérico.

## Entrega a Claude y acceso privado

Para probar todas las pantallas sin habilitar el módulo público:

```powershell
uv run --locked python -m tests.conjuntos_browser
```

Abre `http://127.0.0.1:8894/conjuntos/relaciones/` para el editor y
`http://127.0.0.1:8894/conjuntos/cardinalidad/` para inclusión-exclusión.
El servidor escucha solo en loopback y usa `tests.urls_conjuntos`. Las rutas de
la aplicación normal siguen bloqueadas (404); el catálogo conserva Próximamente.
No hay que cambiar versiones, ramas ni activar rutas públicas para revisar.

La serialización añade `tipo: "par"` con `primero` y `segundo` tipados recursivos.
Las reglas nuevas del procedimiento son `par_ordenado`, `potencia`,
`producto_cartesiano`, `union_intervalos`, `interseccion_intervalos`,
`diferencia_intervalos`, `complemento_intervalos`, `pertenencia_intervalo`
y `relacion_intervalos`. Los gráficos reciben datos del motor; las cadenas solo
se muestran, no se analizan para reconstruir matemáticas.

Claude recibe herramientas funcionales en esta misma rama y PR. Queda su revisión
visual y de interacción final antes de habilitar las URL públicas. No se implementa
comprensión ni demostración simbólica de identidades. El editor estructurado
recursivo es opcional y no sustituye al lector textual seguro.

## Verificación reproducible

`python -m unittest tests.test_conjuntos tests.test_conjuntos_operaciones tests.test_conjuntos_avanzados tests.test_conjuntos_web tests.test_conjuntos_avanzados_web` cubre los diez
casos de aceptación, tipos, anidación, vacío, duplicados, CRUD, renombrado,
referencias, sintaxis, presupuesto acumulado, POST manipulado y escape de texto.
P2 añade tablas de pertenencia exhaustivas sobre los subconjuntos de un universo
de tres elementos, vacío, anidación, exactitud, precedencia, tipos, universos
inválidos, presupuesto de operaciones repetidas y el contrato JSON seguro.
`python -m tests.conjuntos_browser` sirve once escenarios DOM en
`http://127.0.0.1:8894/__pruebas/`: aceptación, guiado, teclado, CRUD, errores
accesibles y resultado desactualizado. No añade dependencias.

P3–P6 añaden comprobaciones de crecimiento previo, pares, generación exacta,
extremos y contactos de intervalos, las ocho regiones de tres conjuntos,
inversión de las 128 distribuciones binarias de regiones y validaciones web.
El runner también prueba zoom, consulta exacta, selección de Venn, edición de
cardinalidades, datos incoherentes y resultados desactualizados. La revisión
física de táctil y lector de pantalla continúa pendiente.
