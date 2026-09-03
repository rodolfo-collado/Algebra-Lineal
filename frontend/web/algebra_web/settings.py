"""Configuración mínima de Django para el entorno de desarrollo local."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-algebra-lineal-development"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "frontend.web.calculadora.apps.CalculadoraConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "frontend.web.algebra_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
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
