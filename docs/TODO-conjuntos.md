# Pendientes del área Conjuntos

[Documentación de Conjuntos](conjuntos.md) · [Índice](README.md)

Seguimiento del plan tras la integración del [PR #104](https://github.com/rodolfo-collado/Algebra-Lineal/pull/104).
P2–P6 y la revisión visual de Claude se completan en la misma rama `feature/conjuntos-p2-operaciones` y el único PR #113.

## P1 — Definición y relaciones entre conjuntos

- [x] Completar la definición y edición de conjuntos finitos y la comprobación de relaciones (PR #104).

### Mejoras pendientes detectadas en pruebas desktop

Estos ajustes no reabren P1, que permanece completado.

- [x] Mejorar el espaciado y la distribución de los botones: filas `A = {…}` con × y «Añadir» junto a su campo.
- [x] Revisar la ubicación de «Guardar cambios» y «Añadir conjunto»: Guardar aparece solo con cambios pendientes; Intro añade.
- [x] Evitar ejemplos precargados: el editor empieza vacío y ofrece cinco ejemplos opcionales.
- [x] Reducir las instrucciones permanentes: una línea de ayuda por campo; la sintaxis vive en «Operaciones disponibles».
- [x] Evaluar el editor estructurado recursivo: se descartó; la lectura por pastillas bajo cada fila muestra los elementos completos sin un segundo modelo.

## P2 — Operaciones finitas

- [x] Implementar unión e intersección.
- [x] Implementar diferencias entre conjuntos.
- [x] Implementar complemento respecto de un conjunto universo explícito.
- [x] Calcular la cardinalidad de conjuntos finitos.
- [x] Admitir expresiones combinadas con agrupación y precedencia de operaciones.

Sintaxis, presupuesto y contrato estructurado para presentación en
[Conjuntos](conjuntos.md#contrato-para-presentación-claude). Las rutas públicas
se habilitaron en P7.

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
- [x] Revisión visual y de interacción (Claude): editor, guía, procedimientos, Venn, recta y cardinalidad en Estudio y Minimalista, claro y oscuro, de 320 px a escritorio.
- [x] Verificar la navegación por teclado: filas de regiones, recta, guía y campos con foco visible.
- [x] Completar las pruebas matemáticas, de integración web y de interacción (14 flujos DOM en Chrome y Edge).
- [x] Probar en la app de escritorio real (WebView2): ambos estilos, claro y oscuro, ventana mínima.
- [ ] Probar con lector de pantalla (NVDA o Narrador).
- [x] Habilitar las rutas y el catálogo después de publicar v0.14.0.

## Posibles extensiones futuras

- [ ] Explorar la definición por comprensión, con dominio y predicados admitidos explícitos.
- [ ] Explorar la comprobación y explicación de identidades de conjuntos.
