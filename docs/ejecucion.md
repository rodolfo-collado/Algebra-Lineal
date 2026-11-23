# Guía de ejecución

[Índice de documentación](README.md) · [Portada](../README.md)

Esta guía sigue la rama `develop`. Para usar el instalador publicado, consulta
[Instalación Windows](instalacion-windows.md). Las interfaces funcionan con
datos locales, sin servidor de base de datos, migraciones ni archivo `.env`.

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
git clone https://github.com/Collado-Labs/Algebra-Lineal.git
cd Algebra-Lineal
git switch develop
uv sync --locked
```

`--locked` obliga a usar las versiones exactas registradas en `uv.lock`; esto
evita que una actualización de una dependencia cambie el comportamiento del
proyecto. El comando crea `.venv/` y deja instaladas las dependencias de
ejecución y el grupo de desarrollo `dev`, que uv incluye por defecto.
[Desarrollo](desarrollo.md#dependencias) describe qué usa cada interfaz.

No es necesario activar `.venv/`: los comandos `uv run` la seleccionan de
forma automática.

## Opción recomendada: interfaz web local

Esta es la forma más simple de usar todas las herramientas visuales durante el
desarrollo. Tras preparar el entorno, ejecuta:

```bash
uv run --locked python manage.py runserver
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en un navegador moderno.
La página de inicio muestra **PyGebra** y cuatro áreas: Álgebra lineal,
Sistemas numéricos, Métodos numéricos y Conjuntos. Mientras la terminal siga ocupada, el
servidor está funcionando; deténlo con `Ctrl+C`.

El servidor de Django escucha solo en tu equipo. No requiere configurar una
base de datos, cuenta, API key ni conexión a Internet después de instalar las
dependencias. Si el puerto 8000 está ocupado, usa otro, por ejemplo:

```bash
uv run --locked python manage.py runserver 8001
```

En ese caso abre `http://127.0.0.1:8001/`.

## Aplicación de terminal

Usa un emulador con Unicode y color, como Windows Terminal en Windows.
La consola interactiva de v0.20.0 se ejecuta desde `develop` con estos comandos
en la raíz del repositorio:

```bash
uv sync --locked
uv run --locked python main.py
```

La consola funciona localmente. Escribe `/` para abrir el menú y entra en
`/resolver` para elegir Álgebra lineal, Sistemas numéricos, Métodos numéricos
o Conjuntos. Al ensanchar la ventana, el chat pasa a la derecha. En ventanas
estrechas queda fijo debajo del historial. En el panel de resultados, el valor
final, el procedimiento y las advertencias se distinguen por su encabezado y
color. El espaciado compacto es el predeterminado. Usa el zoom de tu terminal
para cambiar el tamaño de letra.

| Tecla | Acción |
| --- | --- |
| `↑` y `↓` | Elegir un comando, método o casilla. |
| `←` y `→` | Volver al menú padre o regresar al último submenú visitado. |
| `Enter` | Confirmar una opción, avanzar en un campo de una línea o desplegar un ejercicio enfocado. |
| `Espacio` | Marcar o desmarcar una casilla. En una gráfica de raíces enfocada, reproducir las iteraciones. |
| `F2` | Confirmar una entrada de varias líneas. `Enter` añade una línea. |
| `F3`, `F4`, `F6` | Volver a la pregunta anterior, repetir el último ejercicio o insertar un símbolo matemático. |
| `F7` | Pasar del chat a los resultados o volver al borrador. En una ventana estrecha, amplía el espacio de lectura. |
| `RePág`, `AvPág` | Desplazar los resultados por páginas cuando el panel tiene el foco. |
| `Tab`, `Mayús+Tab` | Cambiar el foco entre controles. |
| `Ctrl+C`, `Ctrl+R`, `Ctrl+T` | Copiar la celda, la fila o la tabla completa en una tabla enfocada. |
| `Esc`, `Ctrl+Q` | Cerrar el menú o ejercicio activo, o salir de PyGebra. |

Las gráficas de raíces muestran los ejes, su escala y los puntos iniciales
del método. Si se detecta un cambio de signo entre muestras del mismo tramo,
la gráfica marca el corte aproximado y muestra los extremos que puedes
probar como intervalo. La consola dibuja la imagen de Matplotlib dentro de
los emuladores que admiten gráficos compatibles y usa una vista de texto con
escala numérica en el resto.

Para pegar en PyGebra puedes usar `Ctrl+V` con el portapapeles interno o el
atajo de pegado de tu terminal para datos de otra aplicación. Las matrices
aceptan celdas separadas por espacios o tabulaciones y filas separadas por
saltos de línea o punto y coma. Si hay un error de formato, aparece debajo
del campo mientras escribes. `F2` mantiene el borrador y el foco hasta que lo
corrijas. Los campos de una línea se confirman con `Enter`.

`/historial` lleva a los ejercicios guardados. Si activas `/debugging`, el
procedimiento incluye enlaces a los archivos del backend ejecutados. En la
lista de archivos, pulsa `Enter` para localizar el archivo o `Ctrl+C` para
copiar su ruta absoluta. La consola guarda el historial y los ajustes en
`consola.sqlite3`, en el directorio local de datos de PyGebra. En Arch Linux
es `${XDG_DATA_HOME:-~/.local/share}/PyGebra/`. En Windows corresponde a
`%LOCALAPPDATA%\PyGebra\`.

En `/ajustes` puedes cambiar el tema, la convención decimal y el espaciado
del procedimiento. La consola guarda estas preferencias junto al historial.

El menú anterior de matrices también está disponible con
`uv run --locked python main.py --clasico`. En ese modo puedes salir con la
opción `9`.

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
con pywebview. **Opciones → Actualizaciones** abre el
[actualizador de escritorio](instalacion-windows.md#actualizar-pygebra). Al cerrar la ventana, el servidor se detiene. En Linux o macOS
la interfaz web es la vía compatible y recomendada para tener todas las
funciones visuales.

La ventana abre maximizada y siempre en Inicio. Entre aperturas recuerda solo
el tema, Exacto/Decimal y la precisión decimal, en
`%LOCALAPPDATA%\PyGebra\preferencias.json`; nunca la sesión de trabajo. Para
volver o avanzar usa los botones laterales del ratón o Alt+← / Alt+→. El clic
derecho ofrece Cortar, Copiar, Pegar y Seleccionar todo; sobre las celdas de
matrices y vectores y el número romano abre el [menú de edición](edicion-entradas.md)
(Rellenar aleatoriamente, Limpiar y, en matrices, Seleccionar). Los atajos propios de
un navegador (F5, Ctrl+P, Ctrl+F, F12) no están activos; para diagnosticar, ejecuta
con `ALGEBRA_DESKTOP_DEBUG=1`, que muestra también las herramientas de desarrollo.

Para un usuario final de Windows no hace falta Git, Python ni uv: descarga
`PyGebra-Setup-<versión>.exe` desde la [última release](https://github.com/Collado-Labs/Algebra-Lineal/releases/latest), instálala y abre **PyGebra** desde el menú Inicio. Consulta [Instalación Windows](instalacion-windows.md) para el detalle de instalación y desinstalación.

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

1. Reducción por filas por Gauss o Gauss-Jordan.
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
| Falta PyInstaller para el build o las pruebas de empaquetado | Incluye el grupo `dev` con `uv sync --locked --group dev`. |

Para construir y probar el instalador de distribución, siguen siendo necesarios
Windows, PowerShell 5.1 o posterior y el grupo de dependencias `dev`.
Consulta [Construir el instalador](instalacion-windows.md#construir-el-instalador)
para ver el requisito de Inno Setup y el proceso de empaquetado.
