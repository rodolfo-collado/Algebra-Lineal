#!/usr/bin/env python
"""Punto de entrada para las tareas de Django del proyecto."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
