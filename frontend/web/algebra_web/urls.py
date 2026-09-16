"""Rutas de la interfaz web."""

from django.urls import include, path


urlpatterns = [
    path("", include("frontend.web.calculadora.urls")),
]
