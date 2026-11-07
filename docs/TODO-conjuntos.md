# Pendientes del área Conjuntos

[Documentación de Conjuntos](conjuntos.md) · [Índice](README.md)

Seguimiento del plan tras la integración del [PR #104](https://github.com/rodolfo-collado/Algebra-Lineal/pull/104).
P2–P6 se completan en la misma rama `feature/conjuntos-p2-operaciones` y el único PR #113; la revisión final corresponde a Claude.

## P1 — Definición y relaciones entre conjuntos

- [x] Completar la definición y edición de conjuntos finitos y la comprobación de relaciones (PR #104).

### Mejoras pendientes detectadas en pruebas desktop

Estos ajustes no reabren P1, que permanece completado.

- [ ] Mejorar el espaciado y la distribución de los botones.
- [ ] Revisar la ubicación de «Guardar cambios» y «Añadir conjunto».
- [ ] Evitar ejemplos precargados innecesarios; considerar la acción «Cargar ejemplo».
- [ ] Reducir las instrucciones y los comentarios permanentes en los formularios.
- [ ] Evaluar el editor estructurado recursivo opcional para conjuntos anidados; el lector textual sigue siendo la entrada segura común.

## P2 — Operaciones finitas

- [x] Implementar unión e intersección.
- [x] Implementar diferencias entre conjuntos.
- [x] Implementar complemento respecto de un conjunto universo explícito.
- [x] Calcular la cardinalidad de conjuntos finitos.
- [x] Admitir expresiones combinadas con agrupación y precedencia de operaciones.

Sintaxis, presupuesto y contrato estructurado para presentación en
[Conjuntos](conjuntos.md#contrato-para-presentación-claude). Se conserva el bloqueo
público; el editor mínimo se comprueba solo con la URLConf de pruebas.

## P3 — Conjunto potencia y producto cartesiano

- [x] Generar el conjunto potencia mediante sus subconjuntos.
- [x] Generar el producto cartesiano con pares ordenados.
- [x] Estimar y controlar el presupuesto computacional antes de generar y presentar resultados.

## P4 — Intervalos

- [x] Implementar operaciones entre intervalos.
- [x] Definir la notación y el tratamiento de extremos abiertos, cerrados e infinitos.
- [x] Representar los intervalos y sus resultados de forma interactiva en la recta real.

## P5 — Diagramas de Venn

- [x] Representar dos y tres conjuntos mediante diagramas de Venn.
- [x] Mostrar los elementos en sus regiones correspondientes.
- [x] Resaltar las regiones asociadas a las operaciones y sus resultados.

## P6 — Cardinalidad interactiva

- [x] Permitir editar las cardinalidades de las regiones.
- [x] Aplicar inclusión-exclusión para obtener las cardinalidades solicitadas.
- [x] Validar la coherencia de los datos de regiones y conjuntos.
- [x] Mostrar los procedimientos de cálculo.

## P7 — Integración final

- [x] Completar la integración del teclado contextual para las nuevas herramientas.
- [x] Actualizar la documentación de uso y las limitaciones.
- [ ] Verificar la accesibilidad y la navegación por teclado.
- [ ] Completar las pruebas matemáticas, de integración web y de interacción desktop.

El acceso público permanece bloqueado hasta la revisión final de Claude. La entrega funcional incluye pruebas matemáticas, HTTP y once flujos de navegador; quedan la revisión visual, la interacción desktop física y el lector de pantalla.

## Posibles extensiones futuras

- [ ] Explorar la definición por comprensión, con dominio y predicados admitidos explícitos.
- [ ] Explorar la comprobación y explicación de identidades de conjuntos.
