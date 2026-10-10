# Documentación de PyGebra

[Volver a la portada](../README.md)

## Usar y comprender

- [Funcionalidades](funcionalidades.md): formatos de entrada, terminal, sistemas,
  vectores, operaciones con matrices (simples y compuestas), conversión de bases y ejemplos para interpretar resultados.
- [Algoritmos](algoritmos.md): implementación manual, aritmética exacta,
  procedimientos estructurados y conexiones entre Ax, combinaciones y sistemas.
- [Instalación Windows](instalacion-windows.md): requisitos, uso y desinstalación;
  también construcción y verificación del paquete para mantenedores.

## Desarrollar y mantener

- [Arquitectura](arquitectura.md): responsabilidades, flujo de ejecución,
  catálogo central e infraestructura desktop.
- [Identidad visual](identidad-visual.md): símbolo oficial de PyGebra, geometría,
  versiones monocromáticas y archivos.
- [Interfaz](interfaz.md): decisiones de UI/UX, accesibilidad,
  componentes compartidos y comportamiento con o sin JavaScript.
- [Desarrollo](desarrollo.md): entorno con uv, ejecución local y cómo extender
  el catálogo sin duplicar navegación o cálculo.
- [Guía de ejecución](ejecucion.md): requisitos, arranque web, terminal o
  escritorio y comprobaciones para usar el proyecto completo.
- [Pruebas](pruebas.md): suite, Django, compilación, enlaces y smoke real Windows.
- [Presupuesto computacional](presupuesto-computacional.md): límite frente a costo,
  cálculo y procedimiento, tamaño de los números, referencias calibrables y
  benchmark. El presupuesto de entrada de Reducción por filas sigue en
  [su propio documento](presupuesto-sistemas.md).
- [Protección numérica común](seguridad-numerica.md): inspección de literales
  antes de convertir, crecimiento exacto acotado y errores controlados.
- [Matrices aumentadas por bloques](matrices-aumentadas.md): primitivas exactas,
  contrato de Gauss-Jordan para `[A | B]`, preparación de `[A | I]` y separación
  de bloques durante el procedimiento.
- [Matriz inversa](matriz-inversa.md): Gauss-Jordan sobre `[A | I]`, la regla
  2×2, verificación, propiedades y aplicación `x = A⁻¹b`.
- [Selección matricial](seleccion-matricial.md): modelo de entrada, gestos,
  comandos sobre A, dimensiones y API interna compartida.
- [Copiado matricial](copiado-matricial.md): copia exacta TSV/HTML, metadata v1,
  prioridad textual y validación estricta de geometría.
- [Pegado matricial](pegado-matricial.md): reglas sobre selecciones, fallback TSV,
  máscaras, atomicidad, huecos/vacíos y preparación para P28.4.
- [Releases](releases.md): SemVer, fuente de versión, promoción por PR,
  publicación desde main con tag/release automáticos y checksums.

La entrada para contribuir sigue siendo [CONTRIBUTING.md](../CONTRIBUTING.md).
Estas guías describen el funcionamiento vigente; el historial de cambios y los
resultados de cada validación se registran en PRs y releases.
