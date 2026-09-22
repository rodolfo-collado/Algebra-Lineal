# Assets de PyGebra

El símbolo oficial es Larga, variante A. La identidad del logo es monocromática.

## Fuente

`svg/pygebra-mark.svg` es el archivo canónico. Usa `fill="currentColor"` y este path:

```text
M2 12H62V34H22V42H40V40L56 46L40 52V50H14V26H54V20H2Z
```

Lienzo `0 0 64 64`. Caja visual `60 × 40` (x=2..62, y=12..52), relación 3:2.

Los demás archivos de esta carpeta se derivan de ese path. No se editan a mano.

## Qué archivo usar

| Contexto | Archivo |
| --- | --- |
| SVG flexible | `svg/pygebra-mark.svg` |
| Negro explícito | `svg/pygebra-mark-black.svg` |
| Blanco explícito | `svg/pygebra-mark-white.svg` |
| Lockup, caja visual | `svg/pygebra-mark-tight.svg` (`viewBox="2 12 60 40"`). No sustituye al master. |
| PNG con transparencia | `png/pygebra-mark-black-<lado>.png` y `png/pygebra-mark-white-<lado>.png` |
| Favicon | `favicon/favicon.svg`, `favicon/favicon.ico`, `favicon/favicon-16x16.png`, `favicon/favicon-32x32.png` |
| Icono de Windows | `app/pygebra.ico` (16, 24, 32, 48, 64, 128, 256) |
| Icono de aplicación, con aire | `app/app-icon-<lado>.png` en negro y `app/app-icon-white-<lado>.png` |

Lados PNG del símbolo: 16, 24, 32, 48, 64, 128, 256 y 512. El fondo es transparente.

En los iconos de aplicación el lienzo de 64 ocupa el 68 % del lado y queda centrado. El símbolo no se estira para llenar el cuadrado.

## Color

| Uso | Claro | Oscuro |
| --- | --- | --- |
| Símbolo | `#000000` | `#FFFFFF` |
| Acento secundario | `#1A6560` | `#7DCFC6` |

El verde es el acento de la interfaz de PyGebra. No es un color del logotipo y no existe un logo verde oficial.

`favicon.svg` pinta el símbolo de negro y, si el sistema está en oscuro, de blanco. Sigue siendo la misma geometría.

## Web

`frontend/web/calculadora/static/calculadora/favicon.svg` y `favicon.ico` son copias generadas. `base.html` las enlaza. El header usa Larga A en negro/blanco: su parcial se sincroniza desde el master con `uv run python scripts/sync_brand_mark.py`.

## Escritorio

`desktop.py`, `AlgebraLineal.spec` y `installer/AlgebraLineal.iss` usan `app/pygebra.ico`.

## Regenerar

Desde la raíz del repositorio, sin dependencias nuevas:

```bash
python scripts/generate_brand_assets.py
```

El script reescribe los SVG, los PNG, los ICO y las copias de favicon que sirve Django.
