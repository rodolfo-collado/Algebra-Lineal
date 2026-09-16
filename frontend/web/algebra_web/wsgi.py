"""Punto de entrada WSGI para servidores locales o de producción futura."""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

application = get_wsgi_application()
