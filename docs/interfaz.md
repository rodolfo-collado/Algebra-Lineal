# Interfaz visual

La aplicación desktop y Django en desarrollo comparten la misma interfaz.

No hace falta un framework frontend: los módulos nuevos reutilizan plantillas
Django, CSS propio y JavaScript mínimo, todos locales.

## Identidad

- Nombre: **Álgebra Lineal**
- Subtítulo: Aprende resolviendo
- Marca: una cuadrícula `[A | b]` en `assets/` y en el header
- Paleta: teal / azul profundo, con equivalencia clara y oscura

El tema claro u oscuro se guarda en `localStorage` (`algebra-lineal-tema`).
Si el usuario no ha elegido, se respeta `prefers-color-scheme`.

Todo debe funcionar sin Internet. No uses Google Fonts, CDN ni iconos remotos.

## Sistema visual

Los estilos están organizados así:

```text
static/calculadora/
├── styles.css              # importa el resto
└── styles/
    ├── tokens.css          # colores, tipografía, radios, sombras
    ├── base.css
    ├── shell.css           # header, navegación, layout
    ├── components.css      # tarjetas, guías, matrices, inicio
    └── modules.css         # formularios y resultados de sistemas
```

Usa tokens semánticos (`--color-brand`, `--color-accent`, `--color-surface-raised`,
…) en lugar de hexadecimales sueltos.

## Guía educativa

`frontend/web/calculadora/guias.py` define mensajes estáticos (`GuiaConcepto`)
para acompañar resultados. No es IA, no hace llamadas externas y no genera
matemática nueva: solo selecciona textos conceptuales según método y
clasificación. El parcial `components/concept_guide.html` los renderiza.

## Cómo añadir un módulo

1. Crea una plantilla que extienda `calculadora/base.html`.
2. Rellena `{% block module_header %}` y `{% block content %}`.
3. Reutiliza `.panel`, `.choice`, `.btn`, `.matrix`, `.concept-guide` y los
   tokens de `static/calculadora/styles/`.
4. Si el módulo muestra matrices, incluye `calculadora/components/matrix.html`.
5. No copies el `<head>`, el header ni el selector de tema.

Hoy solo existe el módulo de sistemas de ecuaciones. No agregues enlaces a
pantallas que todavía no existen.
