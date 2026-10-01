# Protección numérica común (P26.2.1)

[Índice de documentación](README.md)

`backend/seguridad_numerica.py` reúne la inspección de literales y la protección
de racionales calculados. Son comprobaciones de seguridad, independientes de
`presupuesto_computacional`: este último estima el costo de operaciones válidas
y conserva sus categorías, referencias y fórmulas. Una entrada peligrosa se
rechaza; un intermedio extremo termina con un error controlado. Ninguno se
convierte en una advertencia de operación pesada.

## Auditoría de las entradas web

| Camino | Situación anterior | Protección actual |
| --- | --- | --- |
| Sistemas, texto | Ya inspeccionaba constantes, coeficientes e índices antes de `Fraction`/`int`. | Conserva `limitar_entrada=True`, dimensiones, longitud y valores agrupados; importa la inspección común. |
| Sistemas, matriz | Ya inspeccionaba cada celda. | Conserva esa comprobación, ahora desde el módulo común. |
| Matrices: suma, resta, escalar, traspuesta, AB y Ax conocido | `FormularioCeldas` llamaba al conversor sin inspección. | Conversor con `limitar_entrada=True` para todas las celdas y escalares. |
| Vectores: suma, resta y escalar | Componentes y escalar llegaban directamente al conversor. | Activa el mismo modo seguro. |
| Combinación lineal | Generadores y objetivo usaban el conversor sin inspección. | Comparte la protección de Vectores. |
| Resolver Ax = b / ecuaciones matriciales numéricas | A y b heredaban el conversor sin inspección de `FormularioCeldas`. | Comparte la protección de las celdas de Matrices. |
| Matriz inversa (P26.4) | Herramienta nueva. | Celdas de `FormularioCeldas` en modo seguro; Gauss-Jordan y la regla 2×2 operan con `multiplicar_exacto`, `restar_exacto` y `dividir_exacto`; la firma de confirmación usa valores ya leídos. |
| Expresiones: símbolos numéricos (desde P26.6, Operaciones con matrices) | Matrices, vectores y escalares declarados heredaban las celdas sin inspección. | Comparte `FormularioCeldas`. |
| Expresiones: literales en el texto y componentes lineales; A desconocida | El lexer solo tokenizaba enteros, fracciones y decimales, pero no limitaba sus componentes antes de convertirlos. | El parser inspecciona cada token numérico antes del conversor y de `Fraction`. |
| Conversión de bases | Formulario de hasta 128 caracteres y gramática por base antes de acumular dígitos. | Conserva su validación propia. La E hexadecimal es un dígito, no un exponente. |
| Números romanos | Hasta 15 caracteres antes de acumular; arábigos entre 1 y 3999 y símbolos romanos canónicos. | Conserva su validación propia. |
| Dimensiones, cantidades, índices para eliminar símbolos y bases | `IntegerField` con mínimos/máximos, `int` con errores capturados y rangos acotados antes de reservar estructuras; las bases son opciones cerradas. | Conserva estos caminos: `int` no expande notación científica. |

No se reemplaza la gramática de ninguna herramienta. En expresiones, `1e2`
puede significar `1·e2` si se declaró el símbolo `e2`; sin ese símbolo da un
error de símbolo desconocido. El texto completo nunca se interpreta como un
literal científico. En conversión hexadecimal, `1E2` sigue siendo válido.

## Literales antes de convertir

Se extrae la política histórica de [Sistemas](presupuesto-sistemas.md), sin
cambiar sus límites: 100 dígitos por entero, numerador, denominador, parte
entera o parte decimal. Se conservan los signos, espacios y variantes que
ya aceptaba cada parser (`5.` y `1_000` en celdas; los separadores conservan
el cómputo histórico de hasta 100 dígitos en todo el literal).

La inspección no convierte a entero ni calcula potencias. Detecta `e`/`E`
después de un dígito y rechaza `1e1000000000` y `1e-1000000000` antes de
`Fraction`, con el mensaje existente:

> Esta herramienta no admite notación científica. Escribe el número como entero, fracción o decimal.

Si un componente excede el límite:

> El número es demasiado grande para esta herramienta.

`convertir_a_numero(..., limitar_entrada=True)` activa esta inspección antes de
su bloque de conversión para conservar esos mensajes. Todas las entradas web
al conversor la activan o, en las celdas de Sistemas, inspeccionan explícitamente
antes de llamarlo. La consola mantiene su contrato anterior por defecto.
`presupuesto_sistemas.py` reexporta la función, constante y mensajes para
mantener compatibles los consumidores anteriores.

## Valores exactos intermedios y presentación

`validar_valor_exacto` compara los `bit_length()` de `numerator` y `denominator`,
sin convertirlos a texto. El techo nuevo es **12000 bits por componente**
(aproximadamente 3613 cifras), con margen frente a la conversión textual
predeterminada y al redondeo de Exacto/Decimal. Si el entorno configura un
límite textual inferior, se usa el menor entre ese techo y tres veces el límite
configurado: `2**(3*d) < 10**d`. La configuración global solo se consulta;
no se desactiva ni se modifica, incluso si ya estuviera desactivada externamente.

Las primitivas de suma, resta, producto y división comprueban **los dos
operandos antes de operar y el resultado inmediatamente después**. Conservan
`Fraction`, sus cancelaciones y toda la exactitud. Una operación binaria con
operandos acotados puede crear temporalmente enteros de hasta el doble del
techo más una unidad; ese tamaño también queda acotado. El resultado que
excede el techo se rechaza antes de otra operación, instantánea o formato.
Así no se espera a un fallo de `str(int)` ni se acumula crecimiento entre pasos.

Gauss valida la matriz al convertirla a fracciones. Las operaciones elementales
compartidas comprueban los valores antes de copiar, dividir, multiplicar o
restar; el registro valida ambas matrices antes de guardar sus copias.
Gauss-Jordan reutiliza la protección tanto hacia abajo como hacia arriba.
También se protege la sustitución regresiva, la interpretación lineal, cada
producto/acumulación de un producto punto, cadenas de matrices y expresiones
numéricas o lineales. Los formateadores exactos y decimales comprueban el valor
antes de convertir sus enteros a texto, como última defensa.

El error es un `ValueError` con este mensaje visible, capturado por las vistas
existentes, sin traceback ni detalles internos:

> El cálculo produjo números demasiado grandes para mostrarlos de forma segura.

No cambian algoritmos, dimensiones, tamaños máximos, confirmaciones, navegación,
procedimiento plegable, resultado al final ni modos Exacto/Decimal.

## Regresiones

`tests/test_seguridad_numerica.py` vigila `Fraction` en cada clase de entrada
web, comprueba números normales y fronteras históricas, y reproduce crecimiento
con una matriz 6×7 de fracciones admitidas de 100 cifras. Cubre división,
producto, acumulación, eliminación hacia arriba, conservación exacta de los
resultados normales, ausencia de instantáneas del valor rechazado, presentación
y conservación del límite global de Python. Los exponentes peligrosos solo
existen como texto: nunca se construyen enteros de millones de cifras.
