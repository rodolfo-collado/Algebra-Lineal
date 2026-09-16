# Desarrollo

[Índice de documentación](README.md) · [Portada](../README.md)

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado. Consulta su documentación oficial
  para instalarlo en tu sistema.
- Python >= 3.13; el entorno de referencia usa 3.13, fijado en `.python-version`.
  `uv` lo descarga por ti si todavía no lo tienes.
- `colorama`, usada solo para dar color a la terminal.
- `Django`, usado únicamente como capa de presentación web.
- `waitress`, usado como servidor WSGI local de la aplicación desktop.
- `pywebview`, usado para mostrar Django en una ventana nativa.
- `PyInstaller`, disponible como dependencia de desarrollo para generar Windows.

Los cálculos y la interpretación de los sistemas siguen apoyándose en nuestra
implementación del backend y en la biblioteca estándar (`random`, `fractions` y
`re`).

## Preparar el entorno

Desde la raíz del repositorio:

```bash
uv sync --locked
```

`pyproject.toml` declara qué necesita el proyecto y `uv.lock` fija las versiones
exactas que se resolvieron a partir de esa declaración. `uv sync` construye el
entorno en `.venv/` usando ambos archivos, así que todos los colaboradores
trabajan con las mismas versiones.

## Ejecutar desde el código fuente

Desde la raíz del repositorio:

### Terminal

```bash
uv run python main.py
```

Para salir, elige la opción `9` del menú.

### Django

```bash
uv run python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. Es el servidor de desarrollo, no el que usa el
instalador. El recorrido por herramientas está en [Funcionalidades](funcionalidades.md).

### Escritorio en Windows

```bash
uv run python desktop.py
```

El launcher inicia Waitress en loopback y abre pywebview. Consulta
[Arquitectura](arquitectura.md) para su ciclo de vida y
[Distribución Windows](instalacion-windows.md) para construir el instalador.

## Añadir una herramienta

1. Crea su vista y ruta con nombre en `calculadora/urls.py`, y su template en
   `templates/calculadora/modules/<modulo>/`, extendiendo
   `calculadora/layouts/herramienta.html` y rellenando solo los bloques que
   necesite: `tool_context`, `tool_input`, `tool_result`, `tool_explanation` y
   `tool_related`.
2. Regístrala una sola vez en `HERRAMIENTAS`, con ID único y una categoría de
   `CATEGORIAS`. Usa `disponible` y una ruta resoluble cuando funcione;
   `proximamente` no genera enlaces. Una ruta no registrada responde 404.
3. Declara `palabras_clave` con sinónimos que un estudiante escribiría; el
   nombre, la categoría y el área ya forman parte del índice de búsqueda.
4. Define relaciones con IDs existentes en `relacionadas` y una `invitacion`
   breve; `relacionadas_disponibles` excluye destinos aún no disponibles. Las
   relaciones se reservan para módulos realmente distintos: las variantes de
   una misma herramienta (método, bloques del resultado) son opciones de su
   formulario, no herramientas aparte.
5. Si la herramienta necesita símbolos, declara un `TecladoContextual` en
   `teclados.py` con solo las teclas que usa e inclúyelo con
   `components/math_keyboard.html` dentro del contenedor de sus campos. Los
   controles que cambian la estructura (más filas, menos columnas) van aparte,
   nunca dentro del teclado.
6. Añade pruebas de rutas, navegación, búsqueda y comportamiento. Mantén la
   matemática en `backend/` y la presentación en los templates del módulo.

Las decisiones de componentes, accesibilidad y estilo están en
[Interfaz](interfaz.md). Las dependencias y convenciones de commits se mantienen
en [CONTRIBUTING](../CONTRIBUTING.md); las verificaciones previas al PR, en
[Pruebas](pruebas.md). No agregues algoritmos externos que sustituyan la
implementación educativa descrita en [Algoritmos](algoritmos.md).

## Integración y entrega

Trabaja en `feature/*` desde el `develop` actualizado y abre un PR a `develop`.
La promoción estable se realiza mediante otro PR de `develop` a `main`,
conservando ambas historias. No uses reset ni force-push para igualarlas.
El tag solo se crea después de esa promoción, siguiendo [Releases](releases.md).
