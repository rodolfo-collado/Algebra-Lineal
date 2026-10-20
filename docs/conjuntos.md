# Conjuntos: primer incremento

[Índice](README.md) · Herramienta web y desktop: **Conjuntos → Conjuntos finitos → Relaciones entre conjuntos**.

P1 está completado e integrado mediante el [PR #104](https://github.com/rodolfo-collado/Algebra-Lineal/pull/104).
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

## Relaciones y agrupación

El parser principal admite exactamente `operando relación operando`.
Un operando es un nombre definido, un número, un texto o un literal de conjunto.
Los paréntesis agrupan únicamente operandos: `((A)) ⊆ ({1, 2})`.
No hay relaciones encadenadas, operadores ASCII alternativos ni precedencia
de operaciones en P1. `A = {1}` en el editor define A; en **Expresión** compara A
con `{1}` y nunca modifica su definición.

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
llaves, comillas, separador y los seis operadores. El resultado es un único
**Verdadero** o **Falso**, acompañado de un procedimiento inicialmente plegado.

## Capas y protección

- `backend/conjuntos/modelo.py`: `Conjunto` inmutable sobre `frozenset`, números
  `Fraction` y textos. Igualdad y pertenencia usan valores, no el texto escrito.
- `literales.py`: lector de datos y definición `nombre = literal`.
- `parser.py`: árbol `Relacion` / `Referencia`, agrupación y renombrado por tokens.
- `evaluador.py`: resultado booleano y evidencia didáctica, independiente de Django.
- `presupuesto.py`: consumo acumulado antes de construir conjuntos. Comparte
  `LONGITUD_SISTEMA_MAXIMA` (10 000 caracteres), `CELDAS_MAXIMAS` (900 nodos de
  valores, incluidos contenedores y duplicados) y `OPERANDOS_MAXIMOS` (50 conjuntos
  definidos; hasta 50 niveles de lectura contando operandos y agrupaciones).
  La longitud se suma entre nombres, contenidos y expresión. Un POST no obtiene
  un presupuesto nuevo por cada definición. No son límites matemáticos nuevos.
- Formularios, vista y servicio web: contrato HTTP estricto, errores vinculados
  a los campos, evaluación única y adaptación al componente `disclosure`.
  El catálogo sigue siendo la única fuente de navegación y búsqueda.

Se rechazan entradas excesivas, cierres incorrectos, nombres desconocidos,
campos repetidos/ajenos y sintaxis de código. No se utiliza ejecución de Python,
`eval` ni bibliotecas externas de álgebra. Los textos se presentan con escape HTML.
La evidencia tiene un número fijo de pasos; no se genera un paso por combinación
de elementos. `Resultado.estimacion` reutiliza el contrato `Estimacion` del
presupuesto computacional, con trabajo de comparación y presentación separados;
no es una predicción de segundos calibrada para conjuntos.

## Extensiones posteriores, sin implementarlas

El AST separa referencias, valores y relaciones: las operaciones posteriores
podrán ser nodos que produzcan valores para el mismo evaluador. Nuevos tipos
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

No se implementan operaciones, cardinalidad, potencia, producto cartesiano,
intervalos, Venn ni comprensión. Los ajustes detectados en las pruebas desktop
se registran en el [TODO de Conjuntos](TODO-conjuntos.md).

## Verificación reproducible

`python -m unittest tests.test_conjuntos tests.test_conjuntos_web` cubre los diez
casos de aceptación, tipos, anidación, vacío, duplicados, CRUD, renombrado,
referencias, sintaxis, presupuesto acumulado, POST manipulado y escape de texto.
`python -m tests.conjuntos_browser` sirve seis escenarios DOM en
`http://127.0.0.1:8894/__pruebas/`: aceptación, guiado, teclado, CRUD, errores
accesibles y resultado desactualizado. No añade dependencias.
