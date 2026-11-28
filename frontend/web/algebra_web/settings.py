"""Configuración mínima de Django para desarrollo y la aplicación desktop."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-algebra-lineal-development"
)
DESKTOP_MODE = os.environ.get("ALGEBRA_DESKTOP") == "1"
# Lo fija desktop.py: único archivo que la app de escritorio conserva entre aperturas.
DESKTOP_PREFERENCES_FILE = os.environ.get("ALGEBRA_PREFERENCIAS") if DESKTOP_MODE else None
DEBUG = False if DESKTOP_MODE else os.environ.get("DJANGO_DEBUG", "1") == "1"


def _carpeta_usuario():
    """%LOCALAPPDATA%\\PyGebra, la misma carpeta de preferencias.json y consola.sqlite3."""
    base = os.environ.get("LOCALAPPDATA")
    if base and Path(base).is_absolute():
        return Path(base) / "PyGebra"
    try:
        return Path.home() / ".local" / "share" / "PyGebra"
    except RuntimeError:
        return BASE_DIR / ".pygebra"


# Cuaderno de resoluciones. ALGEBRA_RESOLUCIONES aísla pruebas y worktrees de la app instalada;
# sin ella, el navegador de desarrollo usa un archivo propio y la app de escritorio el suyo.
RESOLUCIONES_ARCHIVO = os.environ.get("ALGEBRA_RESOLUCIONES") or str(
    _carpeta_usuario() / ("resoluciones.sqlite3" if DESKTOP_MODE else "resoluciones-desarrollo.sqlite3")
)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "frontend.web.calculadora.apps.CalculadoraConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "frontend.web.calculadora.resoluciones.middleware.ResolucionesMiddleware",
]

ROOT_URLCONF = "frontend.web.algebra_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "frontend.web.calculadora.context_processors.navegacion",
                "frontend.web.calculadora.context_processors.escritorio",
            ],
        },
    },
]

WSGI_APPLICATION = "frontend.web.algebra_web.wsgi.application"
ASGI_APPLICATION = "frontend.web.algebra_web.asgi.application"

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Managua"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
