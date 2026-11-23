"""Punto de entrada de la consola local de PyGebra."""

import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="PyGebra en la terminal")
    parser.add_argument("--clasico", action="store_true", help="Abrir el menú clásico de matrices")
    opciones = parser.parse_args()

    if opciones.clasico:
        from frontend.terminal.menu import ejecutar_menu

        ejecutar_menu()
        return

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
    django.setup()

    from frontend.terminal.graficas import preparar_imagenes
    from frontend.terminal.interfaz import PyGebra

    preparar_imagenes()
    PyGebra().run()


if __name__ == "__main__":
    main()
