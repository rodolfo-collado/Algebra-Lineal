# Interfaz visual

La aplicación desktop y Django en desarrollo comparten la misma interfaz.

No hace falta un framework frontend: los módulos nuevos reutilizan plantillas
Django, CSS propio y JavaScript mínimo, todos locales.

## Identidad

- Nombre: **Álgebra Lineal**
- Subtítulo: Calculadora educativa
- Marca: una cuadrícula `[A | b]` en `assets/` y en el header

El tema claro u oscuro se guarda en `localStorage` (`algebra-lineal-tema`).
Si el usuario no ha elegido, se respeta `prefers-color-scheme`.

Todo debe funcionar sin Internet. No uses Google Fonts, CDN ni iconos remotos.

## Cómo añadir un módulo

1. Crea una plantilla que extienda `calculadora/base.html`.
2. Rellena `{% block module_header %}` y `{% block content %}`.
3. Reutiliza `.panel`, `.choice`, `.btn`, `.matrix` y los tokens de
   `static/calculadora/styles.css`.
4. Si el módulo muestra matrices, incluye `calculadora/_matrix.html`.
5. No copies el `<head>`, el header ni el selector de tema.

Hoy solo existe el módulo de sistemas de ecuaciones. No agregues enlaces a
pantallas que todavía no existen.

## Tokens

Los colores, radios y tipografías viven en `:root` y `[data-theme="dark"]`.
Usa esas variables en lugar de hexadecimales sueltos, para que el próximo
tema del curso herede el mismo lenguaje visual.
