# Identidad visual

[Índice de documentación](README.md) · [Portada](../README.md) · [Assets](../assets/brand/README.md)

La exploración del símbolo está cerrada. Esta página registra la decisión y los archivos. No es un manual de marca.

## PyGebra

El nombre de la identidad es **PyGebra**.

El símbolo es un recorrido que termina avanzando. PyGebra no se limita a entregar un resultado: ayuda a seguir el procedimiento y a ver cómo se conectan los conceptos. El dibujo no representa una letra, ni Python, ni una serpiente, ni un laberinto.

La interfaz web y la ventana de escritorio se presentan como **PyGebra**. Los nombres técnicos históricos de paquetes e instalador se conservan.

## Símbolo

![Símbolo de PyGebra en negro](../assets/brand/svg/pygebra-mark-black.svg)

La variante definitiva es **Larga A**. Es la referencia de esa familia, no una geometría nueva.

El trazo recorre tres tramos horizontales, gira en ángulo recto y el último tramo se convierte en flecha. Esa flecha es el final del recorrido, no una pieza añadida.

## Geometría oficial

La fuente es [`assets/brand/svg/pygebra-mark.svg`](../assets/brand/svg/pygebra-mark.svg).

| | |
| --- | --- |
| `viewBox` | `0 0 64 64` |
| Caja visual | `60 × 40` (x=2..62, y=12..52) |
| Relación | 3:2 |
| Construcción | un solo relleno, derivado de un recorrido de grosor 8 |

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path fill="currentColor" d="M2 12H62V34H22V42H40V40L56 46L40 52V50H14V26H54V20H2Z"/>
</svg>
```

Ese path es la geometría canónica. No se reconstruye a ojo ni se vuelve a separar en trazo y triángulo.

`pygebra-mark-tight.svg` recorta el `viewBox` a `2 12 60 40` para acompañar un texto. El master de iconografía sigue siendo el lienzo de 64.

## Versiones

| Archivo | Relleno |
| --- | --- |
| `pygebra-mark.svg` | `currentColor` |
| `pygebra-mark-black.svg` | `#000000` |
| `pygebra-mark-white.svg` | `#FFFFFF` |

Los tres comparten el mismo path.

### Tema claro

Negro `#000000` sobre blanco `#FFFFFF`.

![Símbolo negro](../assets/brand/png/pygebra-mark-black-64.png)

### Tema oscuro

Blanco `#FFFFFF` sobre negro o casi negro, según la superficie.

<p style="background:#141414;display:inline-block;padding:16px;margin:0">
  <img src="../assets/brand/svg/pygebra-mark-white.svg" alt="Símbolo blanco sobre fondo oscuro" width="64" height="64">
</p>

## Color secundario

| Tema | Color |
| --- | --- |
| Claro | `#1A6560` |
| Oscuro | `#7DCFC6` |

Es un color de acento del producto, no un requisito del logotipo. No hay un logo verde oficial.

La interfaz usa este acento para acciones principales, enlaces, selección y foco. Fondos, superficies, textos y bordes son neutros en ambos temas; los colores se centralizan en `styles/tokens.css`.

## Escala

El símbolo se probó hasta 16 px y sigue reconociéndose. Eso no fija 16 px como un mínimo normativo.

![64 px](../assets/brand/png/pygebra-mark-black-64.png)
![32 px](../assets/brand/png/pygebra-mark-black-32.png)
![24 px](../assets/brand/png/pygebra-mark-black-24.png)
![16 px](../assets/brand/png/pygebra-mark-black-16.png)

## Usos

- **Favicon.** `favicon.svg` y `favicon.ico` en los estáticos de la calculadora. El SVG usa negro y pasa a blanco si el sistema está en oscuro.
- **Escritorio.** `assets/brand/app/pygebra.ico`, referenciado por el launcher, PyInstaller e Inno Setup. En Windows la barra de título usa ese archivo, pero la barra de tareas sigue al acceso directo. El launcher fija el `AppUserModelID` `PyGebra.Desktop` (estable entre versiones) antes de crear la ventana, y los accesos directos declaran el mismo identificador y este icono, no el icono cacheado de `AlgebraLineal.exe`.
- **Aplicación.** `app-icon-192.png`, `app-icon-256.png` y `app-icon-512.png`. El lienzo de 64 ocupa el 68 % del lado, centrado, con el resto transparente. Hay las mismas piezas en blanco.
- **Documentación.** El SVG negro sobre claro y el blanco sobre oscuro. Esta página es el ejemplo.
- **Navegación.** El header combina Larga A y el texto PyGebra. `components/mark.html` deriva del SVG canónico mediante `uv run python scripts/sync_brand_mark.py`; una prueba verifica su sincronización exacta. El símbolo usa el token monocromático `--color-mark`, independiente del acento verde.
- **Tema claro y tema oscuro.** Negro sobre claro, blanco sobre oscuro. Sin sombra ni segundo color dentro del símbolo.

## Lockup

El nombre se escribe `PyGebra` junto al símbolo. Todavía no hay un wordmark en curvas ni una fuente de marca. Esta composición es una referencia, no una regla cerrada: el símbolo y el texto comparten centro vertical, y la separación ronda un tercio de la altura visual del símbolo.

<p>
  <img src="../assets/brand/svg/pygebra-mark-tight.svg" alt="" height="40">
  <span style="font: 600 28px/40px Segoe UI, sans-serif; vertical-align: middle; margin-left: 12px">PyGebra</span>
</p>

## Evitar

- Estirar el símbolo o rotarlo.
- Cambiar la geometría o separar la flecha del recorrido.
- Añadir sombra, gradiente, contorno o cualquier dibujo dentro del símbolo.
- Recolorearlo con un color que no sea negro, blanco o `currentColor` de la superficie.
- Tratar el verde `#1A6560` como color del logo.

Los archivos y el modo de regenerarlos están en [assets/brand/README.md](../assets/brand/README.md).
