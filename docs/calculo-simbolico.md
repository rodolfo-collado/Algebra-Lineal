# Adaptador simbólico de Cálculo

La entrada interna es `adaptar_funcion(texto)`, en `backend.calculo_simbolico`.
Cada llamada crea un `FuncionReal` y traduce su AST validado a objetos SymPy
mediante una lista cerrada. La gramática pública sigue siendo la de `FuncionReal`.

## Contrato

- `texto_original` conserva el texto recibido. `variable` es el símbolo real
  que se usa para sustituir x. `expresion` contiene la fórmula simbólica, con
  cancelación racional acotada cuando procede.
- `dominio.conjunto` contiene el dominio real completo en los casos resueltos.
  Puede ser el conjunto vacío, un intervalo, una unión o un conjunto con polos
  periódicos. `None` indica que quedó alguna condición sin resolver.
- `dominio.restricciones` conserva las condiciones derivadas de cada operación
  original. Cada condición se aplica donde su subexpresión está definida y se
  combina con las demás. Su conjunto individual es `None` si la condición está
  pendiente.
- `dominio.removibles` contiene los puntos confirmados como removibles. En esta
  versión se identifican cuando las exclusiones del dominio son finitas y la
  fórmula racional reducida es regular en el punto. El conjunto vacío también
  puede indicar que el adaptador carece de evidencia suficiente para confirmarlos.

Por ejemplo, `(x²-1)/(x-1)` produce `x+1` con dominio ℝ excepto 1 y un punto
removible en 1. Al evaluar o graficar la fórmula reducida hay que consultar el
dominio original. Para `ln(sen(x))`, se conserva `sen(x)>0` con dominio pendiente.
El dominio describe la función real idealizada. La evaluación con `FuncionReal`
también está sujeta al redondeo, al desbordamiento y al subdesbordamiento.

Los literales decimales se construyen como racionales exactos. π y e se
traducen a sus constantes simbólicas. Para las potencias se comprueba primero
el exponente constante con el evaluador numérico existente. Se conserva el
entero efectivo, π o e con signo, o la fracción exacta cuando concuerda con
el exponente numérico a una unidad de redondeo. Para los demás casos se usa
la representación racional del exponente de máquina y se mantiene su forma
original en `texto_original`. Por ejemplo, `x^(1+1e-30)` tiene exponente efectivo 1.
Una potencia no entera exige base no negativa, o estrictamente positiva
cuando el exponente es negativo.

## Presupuesto y alcance

Se reutilizan los límites de `FuncionReal` de 512 caracteres, 160 nodos y 24
niveles del AST. Un exponente de magnitud mayor que 1024 o inválido en
aritmética real se rechaza con `ValueError`. La traducción mantiene las
operaciones generales sin evaluación automática. La cancelación solo se
ejecuta para árboles racionales con cota estructural de grado 4 y 2048 bits
para los coeficientes. La resolución de restricciones se limita a polinomios
racionales de grado 2 y polos de tangente con argumento afín racional.
Los presupuestos de matrices y conjuntos cuentan otras operaciones.

El adaptador devuelve objetos simbólicos a código interno. Antes de exponer
operaciones simbólicas generales mediante una vista se necesitan presupuestos
propios y aislamiento con cancelación. La derivación, los límites y la
integración quedan para las herramientas posteriores.

## Verificación

    uv lock --check
    uv run --locked python -m unittest -v tests.test_calculo_simbolico
    uv run --locked python -m unittest discover
    uv run --locked python manage.py check

En Windows, `scripts/build_windows.ps1` incluye el adaptador mediante
`AlgebraLineal.spec`, que también incorpora las licencias de SymPy y mpmath.
La compilación del paquete usa el mismo `uv.lock` que la suite.
