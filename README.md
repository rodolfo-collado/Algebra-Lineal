<p align="center">
  <img src="assets/algebra-lineal.svg" alt="Marca de Álgebra Lineal: matriz aumentada" width="80">
</p>

# Álgebra Lineal

**Aprende resolviendo.** Una calculadora educativa que muestra el camino hasta
el resultado y ayuda a conectar sistemas, matrices y vectores.

[![CI](https://github.com/rodolfo-collado/Algebra-Lineal/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rodolfo-collado/Algebra-Lineal/actions/workflows/ci.yml?query=branch%3Amain)
[![Última release](https://img.shields.io/github/v/release/rodolfo-collado/Algebra-Lineal?label=release)](https://github.com/rodolfo-collado/Algebra-Lineal/releases)
![Python >= 3.13](https://img.shields.io/badge/Python-%E2%89%A5%203.13-3776AB?logo=python&logoColor=white)
![Windows x64](https://img.shields.io/badge/Windows-x64-0078D4)

[Instalación](#instalación-en-windows) · [Capacidades](#capacidades) ·
[Documentación](docs/README.md) · [Contribuir](CONTRIBUTING.md)

## Entender el procedimiento

El resultado es solo una parte del ejercicio. Álgebra Lineal permite seguir
las operaciones, comparar métodos y ver por qué un sistema tiene solución
única, infinitas soluciones o ninguna.

- **Procedimientos visibles:** operaciones por filas, sustitución regresiva,
  productos y conversiones acompañados por su desarrollo.
- **Aritmética exacta:** los racionales se conservan como fracciones, sin
  redondear los pasos intermedios.
- **Algoritmos manuales:** el cálculo se implementa con Python estándar,
  sin delegar el álgebra a NumPy, SciPy o SymPy.
- **Conceptos conectados:** un producto `Ax` se puede leer como combinación
  de columnas; resolver `Ax = b` conecta esa lectura con un sistema lineal.
- **Trabajo local:** una vez instalado, funciona sin Internet, con todos
  los recursos de la interfaz incluidos.

La arquitectura separa cálculo y presentación para incorporar nuevas
herramientas educativas sin rehacer los algoritmos ni la navegación.

## Capacidades

### Sistemas de ecuaciones

- Entrada como ecuaciones escritas o matriz aumentada editable.
- Gauss, Gauss-Jordan o comparación de ambos procedimientos.
- Clasificación, columnas pivote y variables libres.
- Solución exacta, solución general o evidencia de la contradicción.

Los dos métodos comparten la interpretación del resultado; puedes comparar
cómo llegan a ella.

### Vectores

- Suma, resta y multiplicación por escalar.
- Comprobación de combinación lineal y sus coeficientes.
- Dimensión variable, con desarrollo componente a componente.

El backend admite dimensión arbitraria; la interfaz limita el tamaño de la
entrada para mantenerla legible.

### Matrices

- Suma, resta, producto por escalar y traspuesta.
- Producto `AB` y producto matriz-vector `Ax`.
- Procedimiento por filas o como combinación lineal de columnas.
- Resolución de `Ax = b`, también con matrices rectangulares.

En `Ax`, x es conocido; en `Ax = b`, la herramienta busca x y explica la
relación entre la ecuación matricial, el sistema y la matriz aumentada.

### Sistemas numéricos

- Conversión de enteros no negativos entre binario, octal, decimal y hexadecimal.
- Divisiones sucesivas y expansión posicional con pasos visibles.
- Conversión entre bases no decimales mostrando el paso intermedio por decimal.

Los formatos de entrada, límites de interfaz y ejemplos completos están en
la [guía de funcionalidades](docs/funcionalidades.md).

## Formas de usar el proyecto

| Interfaz | Uso |
| --- | --- |
| Escritorio Windows | Todas las herramientas visuales en una ventana local. |
| Django en desarrollo | La misma interfaz visual desde el navegador local. |
| Terminal | Menú de matrices y resolución de sistemas por Gauss y Gauss-Jordan. |

La interfaz visual incluye tema claro/oscuro, búsqueda de herramientas y
teclado matemático contextual. La terminal conserva su propio flujo de uso.

## Instalación en Windows

Las distribuciones estables se publicarán en **[GitHub Releases](https://github.com/rodolfo-collado/Algebra-Lineal/releases)**.
El enlace a la **[última versión estable](https://github.com/rodolfo-collado/Algebra-Lineal/releases/latest)**
está preparado; si todavía no hay publicaciones, espera la primera release.
El badge de release se actualizará automáticamente cuando exista una.

Cuando haya una versión publicada:

1. Descarga `AlgebraLineal-Setup-<version>.exe` de sus assets.
2. Ejecuta el instalador y elige si deseas un acceso directo en el escritorio.
3. Abre **Álgebra Lineal** desde el menú Inicio o el acceso directo.

**No necesitas tener Python instalado.** El instalador incluye el runtime y
las dependencias de la aplicación. Se instala para tu usuario y no requiere
privilegios de administrador.

Se admite Windows 10 1809 o posterior / Windows 11, compatible con aplicaciones
x64. Si falta WebView2, su instalación requiere Internet; después la calculadora
funciona offline. El paquete no está firmado digitalmente.

Consulta [Instalación Windows](docs/instalacion-windows.md) para requisitos,
instalación sin conexión y desinstalación, y [Releases](docs/releases.md) para
verificar el SHA-256 del archivo descargado.

Los artifacts de Actions son builds temporales para revisión. La distribución
estable para usuarios se descarga desde Releases.

## Desarrollo rápido

Necesitas Git y [uv](https://docs.astral.sh/uv/), la herramienta que prepara
el entorno Python y sus dependencias desde el archivo de versiones bloqueadas.

```bash
git clone https://github.com/rodolfo-collado/Algebra-Lineal.git
cd Algebra-Lineal
uv sync --locked
uv run python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. El proyecto requiere Python >= 3.13 y `uv` puede
instalar la versión de referencia indicada en `.python-version`.

Para contribuir, crea tu rama a partir de `develop` siguiendo
[CONTRIBUTING.md](CONTRIBUTING.md). Los comandos de terminal, escritorio,
build y verificación se explican en las guías correspondientes.

## Documentación

Empieza por el [índice de documentación](docs/README.md) o elige una guía:

| Guía | Qué encontrarás |
| --- | --- |
| [Funcionalidades](docs/funcionalidades.md) | Entradas, ejemplos, métodos y lectura de resultados. |
| [Algoritmos](docs/algoritmos.md) | Cálculo manual, exactitud y conexiones conceptuales. |
| [Arquitectura](docs/arquitectura.md) | Backend, interfaces y distribución. |
| [Interfaz](docs/interfaz.md) | Identidad visual, componentes, navegación y accesibilidad. |
| [Instalación Windows](docs/instalacion-windows.md) | Uso del instalador y construcción del paquete. |
| [Desarrollo](docs/desarrollo.md) | Entorno local y extensión del catálogo. |
| [Pruebas](docs/pruebas.md) | Suite, verificaciones y smoke del instalador. |
| [Releases](docs/releases.md) | Versionado, promoción a main y entrega automatizada. |

## Contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para el flujo de ramas, las
convenciones de commits y las reglas de implementación matemática.

Las propuestas y correcciones se integran mediante PR a `develop`. Las versiones
estables llegan a `main` mediante un PR separado y se publican desde un tag
validado. Así, documentación, pruebas y distribución acompañan al código.
