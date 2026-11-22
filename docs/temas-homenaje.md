# Temas homenaje

PyGebra incluye tres estilos en honor a los proyectos hermanos del curso:
**ChocoLab**, **BelugaCalc** y **HeyAlgb**. Se eligen en **Opciones → Temas
homenaje**, junto a Estudio y Minimalista, y funcionan en tema claro y oscuro.

Son **estilos**, no aplicaciones alternativas: conservan el símbolo y el nombre de
PyGebra, la navegación, el catálogo, las herramientas, el teclado matemático y la
lectura de resultados. Solo cambian colores, radios y algunos detalles de navegación.

## Cómo están hechos

- `data-estilo` admite `chocolab`, `belugacalc` y `heyalgb`, además de `estudio` y
  `minimalista`. La lista vive en `preferencias.py` (`pygebra-estilo`) y en
  `tema_inicial.html` (`preferencias.estilo()`), que `opciones.js` reutiliza al volver
  del historial.
- `styles/homenajes.css` se carga después de `estudio.css`. Parte de la forma sobria
  (la de Minimalista, sin la habitación) y redefine los tokens de `tokens.css` bajo
  `[data-estilo="…"][data-theme="light|dark"]`. Por eso formularios, tablas, avisos,
  el foco, Venn y las gráficas de Plotly (que leen los tokens al cambiar
  `data-estilo`) heredan el tema sin tocar su plantilla.
- En Inicio, `components/homenaje_firma.html` muestra la firma «En honor a …» con el
  logotipo original del equipo, solo para el estilo activo. En Opciones, cada tema
  homenaje lleva su logotipo y la misma dedicatoria.

## Decisiones visuales

| Tema | Tomado del proyecto | Cómo se adapta a PyGebra |
|---|---|---|
| ChocoLab | Paletas clara y oscura de `static/css/estilos.css`: crema `#F8F5F0`, papel `#FFFDF9`, tinta `#382417`, cacao `#6C3B28`, cobre `#B4744C`; noche `#171310` / `#211A16` / `#F5E9DB` / `#D4A177`. Tarjetas amplias, radios suaves, sombra tenue. | Cacao como acento de texto y botón primario (8.4:1); el cobre (3.5:1) queda para foco y detalles, nunca para texto. Radios de 12–16 px. |
| BelugaCalc | Barra lateral `#063D89`, círculo activo `#62B9FF` con icono `#1A1C29`, fondo claro `#F8FAFC`/hielo. | La cabecera de PyGebra se vuelve barra marina en ambos temas; la herramienta activa del menú y de la mesa es una cápsula celeste con texto oscuro (7.9:1). Fondo hielo `#F4F8FB`; de noche, superficies marinas. |
| HeyAlgb | `core/ui/tema.py`: negro `#060606`, panel `#4D0000`, encabezado `#8F0000`, acento `#FE0000`, ámbar `#FFCC00` para advertencias; esquinas rectas y bordes firmes. | Oscuro como variante principal; claro con superficies neutras y acento granate. Franja roja de 3 px bajo la cabecera, radios de 2–3 px, botón primario en versalitas y herramienta activa en bloque sólido. El error usa un carmín distinto del acento y siempre lleva su texto. |

Lo que **no** se trasladó: tipografías propias (DM Sans/Manrope vía Google Fonts,
Poppins, Impact y las fuentes de HeyAlgb), la barra lateral animada de BelugaCalc, la
estética Persona 5 de HeyAlgb y cualquier sonido o música. PyGebra sigue con sus
fuentes del sistema y sus componentes.

## Verificación de contraste

Calculado con la fórmula de luminancia relativa de WCAG 2.2 sobre los tokens finales
(mínimos: texto 4.5:1; bordes de campo y foco 3:1). Ningún par queda por debajo.

| Par | ChocoLab claro | ChocoLab oscuro | BelugaCalc claro | BelugaCalc oscuro | HeyAlgb claro | HeyAlgb oscuro |
|---|---|---|---|---|---|---|
| Texto / fondo | 13.48 | 15.44 | 15.12 | 15.77 | 17.74 | 18.59 |
| Texto secundario / fondo | 6.06 | 7.66 | 6.27 | 9.44 | 7.81 | 9.55 |
| Texto secundario / superficie atenuada | 5.52 | 6.46 | 5.87 | 7.07 | 7.20 | 7.95 |
| Acento / superficie | 9.01 | 7.49 | 10.31 | 7.39 | 9.69 | 5.21 |
| Texto del botón primario / acento | 8.68 | 7.96 | 10.31 | 8.45 | 9.69 | 5.73 |
| Error / fondo del error | 5.57 | 6.24 | 6.97 | 5.80 | 6.69 | 7.87 |
| Éxito / fondo del éxito | 5.10 | 7.41 | 5.38 | 6.44 | 5.38 | 7.22 |
| Advertencia / fondo | 4.96 | 6.57 | 4.96 | 6.69 | 4.96 | 10.26 |
| Borde de campo / superficie | 4.05 | 3.75 | 3.34 | 4.56 | 4.62 | 4.54 |
| Foco / fondo | 3.48 | 10.21 | 9.66 | 8.43 | 4.60 | 5.73 |

Detalles propios: cápsula celeste de BelugaCalc 7.97 (claro) y 8.45 (oscuro); texto
blanco sobre la barra marina 10.31 y 14.92; foco celeste sobre la barra 4.86 y 7.04.

## Créditos y procedencia de los archivos

Los equipos autorizaron a PyGebra a usar sus recursos gráficos propios. Se incorporan
**solo sus logotipos**, sin modificar, en `frontend/web/calculadora/static/calculadora/homenajes/`.

| Archivo en PyGebra | Origen (repositorio, commit, ruta) | Autoría | SHA-256 |
|---|---|---|---|
| `chocolab.png` (1206×389) | [juliosevillag04/chocolab-prueba1](https://github.com/juliosevillag04/chocolab-prueba1) `95ef537`, `static/img/chocolab.png` | Equipo ChocoLab | `0c6148ddcd6d4baa68a523ee3e4a7f76fecc94095073974fb45ba8f59c497a9e` |
| `belugacalc.png` (500×500) | [Mirai1602/BelugaTeam](https://github.com/Mirai1602/BelugaTeam) `8099a6d`, `assets/BelugaK1.png` | Equipo BelugaCalc | `ada23ad0f4374bc804b967084f0a551cbd38f20fd115c38aa15af956c7db2909` |
| `heyalgb.png` (1280×1280) | [OscarDU24/Algebra-Lineal-](https://github.com/OscarDU24/Algebra-Lineal-) `2ab7621`, `core/assets/HeyAlgbLogoBlanco.png` | Equipo HeyAlgb (logo del proyecto; su inventario pide confirmar autoría) | `169c9d45e372efb341ba214f9173d60aa2c588efc249e0c6c6e1221db0a9b460` |

Ninguno de los tres repositorios declara una licencia; el uso se apoya en el permiso
de los equipos. Si un equipo lo retira, basta con borrar su PNG y su firma.

### Recursos revisados y descartados

| Recurso | Motivo |
|---|---|
| `BackgroundMusic.mp3` y efectos de HeyAlgb | Pista de la banda sonora comercial de Persona 5 y efectos extraídos de un juego (su propio `docs/RECURSOS_Y_LICENCIAS.md`). |
| `HelveticaNowDisplay-Bold.ttf`, `Democratica Bold.ttf` | Fuentes comerciales (Monotype, Emigre). |
| `UltraCondensedSansSerif.ttf` | Licencia sin confirmar. |
| Fuentes OFL de HeyAlgb (Anton, Archivo Black, League Spartan…) | Libres, pero innecesarias: añadirían peso y el aviso OFL sin mejorar la lectura. |
| DM Sans y Manrope (ChocoLab), Poppins (BelugaCalc) | Se cargan desde Google Fonts o el sistema; PyGebra funciona sin red. |
| `logofia.png` (ChocoLab), `UAMICON.png` (HeyAlgb) | Logotipos institucionales: el permiso de los equipos no los cubre. |
| Avatares, fondos e iconos de módulos de HeyAlgb | Origen no documentado; los avatares podrían derivar de arte oficial. |
| `HeyAlgbICON.png` | Mismo símbolo en negro sobre fondo opaco; se prefirió la versión blanca, que se lee sobre la ficha granate. |

## Capturas

Las comparativas de los tres temas (Inicio y Sistemas lineales Ax = b, claro y
oscuro, escritorio y 390 px) están en `docs/capturas/temas-homenaje/`.
