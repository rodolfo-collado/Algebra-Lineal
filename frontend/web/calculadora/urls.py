"""Rutas de la calculadora web."""

from django.urls import path

from . import views


app_name = "calculadora"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("matrices/reduccion/", views.sistemas, name="reduccion-filas"),
    # Compatibilidad: GET redirige; POST raíz reutiliza la vista y slugs preservan el cuerpo.
    path("sistemas/", views.sistemas_ruta_antigua, name="sistemas"),
    path("sistemas/<slug:herramienta>/", views.sistemas_ruta_antigua, name="sistemas-antigua"),
    path("vectores/operaciones/", views.operaciones_vectores, name="operaciones-vectores"),
    path("matrices/operaciones/", views.operaciones_matrices, name="operaciones-matrices"),
    # Compatibilidad: Expresiones matriciales es ahora Operaciones con matrices (GET 301, POST 308).
    path("matrices/expresiones/", views.expresiones_ruta_antigua, name="expresiones-matriciales"),
    path("matrices/ecuaciones/", views.ecuaciones_matriciales, name="ecuaciones-matriciales"),
    path("matrices/inversa/", views.matriz_inversa, name="matriz-inversa"),
    path("bases/conversion/", views.conversion_bases, name="conversion-bases"),
    path("romanos/conversion/", views.conversion_romanos, name="conversion-romanos"),
    # Solo la app de escritorio: tema y formato numérico entre aperturas (404 en la web).
    path("preferencias/", views.guardar_preferencia, name="preferencias"),
]
