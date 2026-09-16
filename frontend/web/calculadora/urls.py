"""Rutas de la calculadora web."""

from django.urls import path

from . import views


app_name = "calculadora"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("sistemas/", views.sistemas, name="sistemas"),
    # Compatibilidad con las rutas de P10.1 (/sistemas/gauss/, …): redirigen a /sistemas/.
    path("sistemas/<slug:herramienta>/", views.sistemas_ruta_antigua, name="sistemas-antigua"),
    path("vectores/operaciones/", views.operaciones_vectores, name="operaciones-vectores"),
    path("matrices/operaciones/", views.operaciones_matrices, name="operaciones-matrices"),
    path("matrices/ecuaciones/", views.ecuaciones_matriciales, name="ecuaciones-matriciales"),
    path("bases/conversion/", views.conversion_bases, name="conversion-bases"),
]
