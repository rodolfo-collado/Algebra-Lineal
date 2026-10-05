<p align="center">
  <img src="assets/brand/svg/pygebra-mark-black.svg" alt="Símbolo de PyGebra" width="80">
</p>

# PyGebra

**Aprende resolviendo.** Una calculadora educativa que muestra el camino hasta
el resultado y ayuda a conectar sistemas, matrices y vectores.

[![CI](https://github.com/rodolfo-collado/Algebra-Lineal/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/rodolfo-collado/Algebra-Lineal/actions/workflows/ci.yml?query=branch%3Adevelop)
[![Última release](https://img.shields.io/github/v/release/rodolfo-collado/Algebra-Lineal?label=release)](https://github.com/rodolfo-collado/Algebra-Lineal/releases/latest)
![Python >= 3.13](https://img.shields.io/badge/Python-%E2%89%A5%203.13-3776AB?logo=python&logoColor=white)
![Windows x64](https://img.shields.io/badge/Windows-x64-0078D4)

[Capacidades](#capacidades) · [Instalación](#instalación-en-windows) ·
[Desarrollo](#desarrollo-rápido) · [Documentación](docs/README.md) · [Contribuir](CONTRIBUTING.md)

PyGebra permite seguir las operaciones, comparar métodos y entender por qué un
sistema tiene solución única, infinitas soluciones o ninguna. Conserva los
racionales como fracciones y permite mostrar resultados exactos o decimales
(2, 4, 6 u 8 posiciones), sin recalcular. Los algoritmos se implementan
manualmente con Python estándar. Una vez instalado, funciona sin Internet.

## Capacidades

### Vectores

- Suma, resta y multiplicación por escalar, con desarrollo componente a componente.
- Combinación lineal: comprobación y cálculo de sus coeficientes.

### Matrices

- **Operaciones con matrices:** suma, resta, escalar, traspuesta, productos
  `AB` y `Ax`, expresiones combinadas e igualdades. También determina una matriz
  desconocida en `Ax = b` con un vector simbólico.
- **Reducción por filas:** Gauss, Gauss-Jordan o comparación de ambos, desde
  ecuaciones o una matriz aumentada; muestra pivotes, variables libres y solución.
- **Resolver Ax = b:** encuentra x con A y b conocidos, también para matrices
  rectangulares, y explica la relación con el sistema lineal.
- **Matriz inversa:** Gauss-Jordan o regla directa para 2×2; explica cuándo no
  existe y permite verificar `A·A⁻¹ = I` y `A⁻¹·A = I`.
- **Propiedades y aplicación de la inversa:** `(A⁻¹)⁻¹ = A`,
  `(AB)⁻¹ = B⁻¹A⁻¹`, `(Aᵀ)⁻¹ = (A⁻¹)ᵀ` y `x = A⁻¹b`.
  Esta aplicación requiere A invertible; **Resolver Ax = b** sigue siendo la
  herramienta general para hallar x.

Consulta [Funcionalidades](docs/funcionalidades.md) y
[Matriz inversa](docs/matriz-inversa.md) para entradas, ejemplos y procedimientos.
Los cálculos largos piden confirmación según el
[presupuesto computacional](docs/presupuesto-computacional.md).

### Sistemas numéricos

- Conversión entre binario, octal, decimal y hexadecimal, incluidos negativos,
  a uno o varios destinos, con divisiones sucesivas y expansión posicional.
- Conversión entre números arábigos y romanos, del 1 al 3999, en ambos sentidos.

## Formas de usar el proyecto

| Interfaz | Uso |
| --- | --- |
| Escritorio Windows | Herramientas visuales en una ventana local. |
| Django en desarrollo | La misma interfaz desde el navegador local. |
| Terminal | Matrices y sistemas por Gauss y Gauss-Jordan. |

La interfaz visual incluye tema claro/oscuro, búsqueda de herramientas y
teclado matemático contextual.

## Instalación en Windows

Descarga el instalador desde la
**[última versión estable](https://github.com/rodolfo-collado/Algebra-Lineal/releases/latest)**.
Todas las versiones publicadas están en
[GitHub Releases](https://github.com/rodolfo-collado/Algebra-Lineal/releases).

1. Descarga `PyGebra-Setup-<version>.exe`.
2. Ejecuta el instalador y elige si deseas un acceso directo en el escritorio.
3. Abre **PyGebra** desde el menú Inicio o el acceso directo del escritorio.

**No necesitas Python instalado.** El paquete incluye el runtime y las
dependencias, se instala para tu usuario y no requiere permisos de administrador.

Se admite Windows 10 1809 o posterior / Windows 11, compatible con aplicaciones
x64. Si falta WebView2, su instalación requiere Internet; después PyGebra funciona
sin conexión. El paquete no está firmado digitalmente.

Consulta [Instalación Windows](docs/instalacion-windows.md) para requisitos,
instalación sin conexión y desinstalación, y
[Releases](docs/releases.md#verificar-una-descarga) para verificar el SHA-256.
Los artifacts de Actions son builds temporales para revisión.

## Desarrollo rápido

Necesitas Git y [uv](https://docs.astral.sh/uv/), que prepara el entorno Python
y sus dependencias desde el archivo de versiones bloqueadas.

```bash
git clone https://github.com/rodolfo-collado/Algebra-Lineal.git
cd Algebra-Lineal
uv sync --locked
uv run python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. Se requiere Python >= 3.13; uv puede instalar
la versión indicada en `.python-version`. Consulta [Desarrollo](docs/desarrollo.md)
para el entorno y [Guía de ejecución](docs/ejecucion.md) para terminal y escritorio.

## Documentación

El [índice de documentación](docs/README.md) reúne las guías de uso,
algoritmos, arquitectura, interfaz, pruebas y distribución.

- [Funcionalidades](docs/funcionalidades.md): entradas, ejemplos y resultados.
- [Matriz inversa](docs/matriz-inversa.md): métodos, verificación, propiedades y aplicación.
- [Pruebas](docs/pruebas.md): verificaciones locales, CI y smoke Windows.
- [Releases](docs/releases.md): versión, promoción a main y publicación automática.

## Contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para las convenciones y reglas de
implementación. Crea tu rama desde `develop` y abre un PR hacia esa rama.

Las versiones se preparan antes del PR `develop → main`. Su merge autoriza la
publicación: GitHub Actions valida el candidato, ejecuta CI y crea automáticamente
el tag y la release cuando todas las comprobaciones pasan.
