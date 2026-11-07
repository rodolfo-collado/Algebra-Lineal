# Conjuntos: definición, relaciones y operaciones finitas

[Índice](README.md) · Herramienta web y desktop: **Conjuntos → Conjuntos finitos → Relaciones entre conjuntos**.

P1 está completado e integrado mediante el [PR #104](https://github.com/rodolfo-collado/Algebra-Lineal/pull/104).
P2 extiende su parser y evaluador con operaciones finitas y cardinalidad.
El acceso público está temporalmente bloqueado: Conjuntos figura como
**Próximamente**, igual que Cálculo, y las URL `/conjuntos/…` responden 404.
La implementación, los avances y la documentación que sigue se conservan.
Las pruebas matemáticas siguen activas; las del editor usan una URLConf exclusiva
de pruebas, que no habilita el módulo en la aplicación ni en el ejecutable.
Consulta el [TODO de Conjuntos](TODO-conjuntos.md) para las fases P2–P7, las mejoras
detectadas en las pruebas desktop y las posibles extensiones futuras.

## Definir y editar

En **Nueva definición**, escribe `A = {1, 2, {3, 4}, "rojo"}` y pulsa
**Añadir conjunto**. Cada definición tiene nombre y contenido editables por
separado. **Guardar cambios** aplica la edición sin calcular; **Comprobar relación**
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
Un operando es un nombre definido, un número, un texto, un literal o una operación.
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

Las cinco operaciones exigen conjuntos finitos. El universo del complemento es
un segundo argumento obligatorio y puede ser una expresión: `∁(A, A ∪ B)`.
No se infiere un universo de otros conjuntos definidos y se rechaza A si contiene
algún elemento ajeno a U. No hay complemento unario ni función con nombre reservado.
La diferencia utiliza **U+2216 `∖`**, no barra inversa ni el signo de resta.

Precedencia, de mayor a menor: agrupaciones, `∁(…, …)` y `|…|`; después `∩`;
después `∪` y `∖`, con igual prioridad y asociación a la izquierda; al final la
relación opcional. Así `A ∪ B ∩ C` significa `A ∪ (B ∩ C)` y `A ∖ B ∪ C`
significa `(A ∖ B) ∪ C`. Usa `A ∖ (B ∪ C)` si quieres excluir ambos.
La cardinalidad produce un número, por lo que `|A| ∪ B` se rechaza por tipos.
Los conjuntos anidados siguen siendo elementos completos: `|{1, {1}, {{1}}}| = 3`.
Las definiciones siguen admitiendo solamente literales; `S = A ∪ B` no define S.

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
El editor y el teclado existentes permiten probar P2 con la URLConf de pruebas;
el refinamiento visual, Estudio y Minimalista quedan fuera de este incremento.

## Extensiones posteriores, sin implementarlas

El AST separa referencias, valores, operaciones y relaciones. Nuevos tipos
inmutables (pares e intervalos) extenderán el dominio de elementos y su
presentación, manteniendo las reglas de conjuntos finitos.

**Pares e intervalos:** reservar sintaxis explícita `par(1, 2)` e
`intervalo(1, 2, abierto, abierto)`. `(1,2)` está rechazado en P1 y no debería
adquirir dos significados según el contexto. Cualquier notación abreviada futura
deberá tener un marcador inequívoco; los paréntesis actuales siguen agrupando.

**Editor estructurado opcional:** se pospone. La cuadrícula de vectores presupone
posiciones numéricas y dimensión común; no representa un árbol heterogéneo.
Propuesta: una lista por conjunto con «Añadir elemento» y tipo número/texto/conjunto;
elegir conjunto despliega otra lista sin nombre. Cada fila genera el mismo literal
seguro y pasa por `analizar_literal`, con presupuesto acumulado. Reutilizaría
tarjetas, etiquetas, botones y teclado; no el controlador de dimensiones ni un
segundo modelo o evaluador. P1 conserva la entrada textual como única modalidad
de definición.

No se implementan potencia, producto cartesiano,
intervalos, Venn ni comprensión. Los ajustes detectados en las pruebas desktop
se registran en el [TODO de Conjuntos](TODO-conjuntos.md).

## Verificación reproducible

`python -m unittest tests.test_conjuntos tests.test_conjuntos_operaciones tests.test_conjuntos_web` cubre los diez
casos de aceptación, tipos, anidación, vacío, duplicados, CRUD, renombrado,
referencias, sintaxis, presupuesto acumulado, POST manipulado y escape de texto.
P2 añade tablas de pertenencia exhaustivas sobre los subconjuntos de un universo
de tres elementos, vacío, anidación, exactitud, precedencia, tipos, universos
inválidos, presupuesto de operaciones repetidas y el contrato JSON seguro.
`python -m tests.conjuntos_browser` sirve ocho escenarios DOM en
`http://127.0.0.1:8894/__pruebas/`: aceptación, guiado, teclado, CRUD, errores
accesibles y resultado desactualizado. No añade dependencias.

Para P3 quedan por decidir el modelo de pares ordenados (distinto de un conjunto
de dos elementos), la sintaxis definitiva `par(…)`/operaciones de potencia y
producto, y la estimación previa del crecimiento exponencial o cartesiano.
El presupuesto de P2 limita recorridos finitos: P3 deberá reservar el tamaño de
generación y de presentación **antes** de enumerar resultados. No habilitar rutas
públicas hasta completar P7 y sus verificaciones de integración.
