# Guía de ejecución

[Índice de documentación](README.md) · [Portada](../README.md)

Esta guía explica cómo ejecutar PyGebra desde el código fuente y qué se necesita
para disponer de todas sus funciones. El proyecto no usa base de datos ni
variables de entorno obligatorias: no hace falta ejecutar migraciones ni crear
un archivo `.env`.

## Requisitos comunes

Para trabajar desde el repositorio necesitas:

- Git, solo si aún debes clonar el proyecto.
- [uv](https://docs.astral.sh/uv/), que crea y administra el entorno virtual.
- Conexión a Internet la primera vez, para que uv descargue Python y las
  dependencias bloqueadas en `uv.lock`.
- Python 3.13 o superior. No hace falta instalarlo manualmente: `uv` descarga
  la versión indicada por `.python-version` si no está disponible.

Desde una terminal, sitúate en la raíz del proyecto y prepara el entorno:

```bash
git clone https://github.com/rodolfo-collado/Algebra-Lineal.git
cd Algebra-Lineal
uv sync --locked
```

`--locked` obliga a usar las versiones exactas registradas en `uv.lock`; esto
evita que una actualización de una dependencia cambie el comportamiento del
proyecto. El comando crea `.venv/` y deja instalados Django, pywebview,
Waitress y colorama. Para ejecutar la suite completa de pruebas o construir el
instalador, añade las dependencias de desarrollo:

```bash
uv sync --locked --group dev
```

No es necesario activar `.venv/`: los comandos `uv run` la seleccionan de
forma automática.

## Opción recomendada: interfaz web local

Esta es la forma más simple de usar todas las herramientas visuales durante el
desarrollo. Tras preparar el entorno, ejecuta:

```bash
uv run --locked python manage.py runserver
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en un navegador moderno.
La página de inicio debe mostrar **PyGebra** y las secciones de sistemas,
vectores, matrices y sistemas numéricos. Mientras la terminal siga ocupada, el
servidor está funcionando; deténlo con `Ctrl+C`.

El servidor de Django escucha solo en tu equipo. No requiere configurar una
base de datos, cuenta, API key ni conexión a Internet después de instalar las
dependencias. Si el puerto 8000 está ocupado, usa otro, por ejemplo:

```bash
uv run --locked python manage.py runserver 8001
```

En ese caso abre `http://127.0.0.1:8001/`.

## Alternativa: aplicación de terminal

La terminal permite operar matrices y resolver sistemas con Gauss y
Gauss-Jordan. Funciona en Windows, Linux y macOS:

```bash
uv run --locked python main.py
```

Sigue las opciones numeradas del menú. Para salir, selecciona la opción `9`.
Esta modalidad no incluye los módulos visuales de vectores, conversión de
bases ni el teclado matemático; para la experiencia completa usa la interfaz
web local o la aplicación de escritorio de Windows.

## Aplicación de escritorio (Windows)

La versión desktop abre la misma interfaz visual en una ventana nativa. Para
ejecutarla desde el código fuente necesitas, además de los requisitos comunes:

- Windows 10 versión 1809 o posterior, o Windows 11, de 64 bits.
- Microsoft Edge WebView2 Runtime actualizado. Conéctate a Internet para que
  el instalador lo obtenga si falta, o instálalo previamente mediante el
  [instalador Evergreen Standalone de Microsoft](https://developer.microsoft.com/microsoft-edge/webview2/).

Después de `uv sync --locked`, ejecuta desde PowerShell o CMD:

```powershell
uv run --locked python desktop.py
```

PyGebra inicia un servidor local Waitress en `127.0.0.1` y muestra su contenido
con pywebview. Al cerrar la ventana, el servidor se detiene. En Linux o macOS
la interfaz web es la vía compatible y recomendada para tener todas las
funciones visuales.

Para un usuario final de Windows no hace falta Git, Python ni uv: descarga
`AlgebraLineal-Setup-<versión>.exe` desde la [última release](https://github.com/rodolfo-collado/Algebra-Lineal/releases/latest), instálala y abre **Álgebra Lineal** desde el menú Inicio. Consulta [Instalación Windows](instalacion-windows.md) para el detalle de instalación y desinstalación.

## Comprobar que quedó listo

Antes de usar o entregar el proyecto, ejecuta estas verificaciones desde la
raíz:

```bash
uv run --locked python manage.py check
uv run --locked python -m unittest discover -s tests
```

El primer comando debe terminar con `System check identified no issues`; el
segundo debe terminar con `OK`. Para una comprobación manual de la interfaz,
inicia el servidor web y verifica que puedes:

1. Resolver un sistema por Gauss o Gauss-Jordan.
2. Sumar o multiplicar matrices.
3. Calcular una operación con vectores.
4. Convertir un número entre bases.
5. Cambiar entre formato exacto y decimal cuando haya resultados fraccionarios.

Si todas estas pruebas funcionan, están disponibles las funcionalidades
principales del proyecto desde el código fuente.

## Problemas frecuentes

| Situación | Qué hacer |
| --- | --- |
| `uv` no se reconoce | Instala uv y abre una terminal nueva para que su ruta quede disponible. |
| uv no puede descargar Python o paquetes | Conéctate a Internet y vuelve a ejecutar `uv sync --locked`. Después podrá funcionar sin conexión mientras `.venv/` permanezca intacto. |
| El navegador no abre la página | Comprueba que `runserver` sigue activo y usa exactamente la dirección que muestra la terminal. |
| El puerto 8000 está ocupado | Inicia Django con otro puerto, por ejemplo `runserver 8001`. |
| La ventana de Windows informa que falta WebView2 | Instala o actualiza WebView2 Runtime y vuelve a abrir `desktop.py`. |
| Las pruebas necesitan PyInstaller | Ejecuta `uv sync --locked --group dev` antes de correrlas. |

Para construir y probar el instalador de distribución, siguen siendo necesarios
Windows, PowerShell 5.1 o posterior, Inno Setup 6.3 o posterior y el grupo de
dependencias `dev`. El proceso está documentado en
[Instalación Windows](instalacion-windows.md#construir-el-instalador).
