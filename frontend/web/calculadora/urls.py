"""Rutas de la calculadora web."""

from django.urls import path

from . import views
from .views_raices import (explorar_funcion, newton_raphson_ruta_antigua, resolver_biseccion, resolver_newton_raphson,
                           resolver_regla_falsa, resolver_secante)
from .views_conjuntos import relaciones_conjuntos, cardinalidades_conjuntos


app_name = "calculadora"


urlpatterns = [
    # Métodos abiertos: una herramienta con un método por ruta; la gráfica de Newton añade f′(x).
    path("metodos-numericos/metodos-abiertos/newton-raphson/", resolver_newton_raphson, name="newton-raphson"),
    path("metodos-numericos/metodos-abiertos/newton-raphson/grafica/", explorar_funcion, {"derivar": True}, name="newton-raphson-grafica"),
    path("metodos-numericos/metodos-abiertos/secante/", resolver_secante, name="secante"),
    path("metodos-numericos/metodos-abiertos/secante/grafica/", explorar_funcion, name="secante-grafica"),
    # Compatibilidad: Newton-Raphson era una herramienta aparte (GET 301 con la consulta, POST 308).
    path("metodos-numericos/newton-raphson/", newton_raphson_ruta_antigua, name="newton-raphson-antigua"),
    path("metodos-numericos/newton-raphson/grafica/", newton_raphson_ruta_antigua, {"grafica": True}),
    path("conjuntos/relaciones/", relaciones_conjuntos, name="relaciones-conjuntos"),
    path("conjuntos/cardinalidad/", cardinalidades_conjuntos, name="cardinalidades-conjuntos"),
    path("metodos-numericos/biseccion/", resolver_biseccion, name="biseccion"),
    path("metodos-numericos/biseccion/grafica/", explorar_funcion, name="biseccion-grafica"),
    path("metodos-numericos/regla-falsa/", resolver_regla_falsa, name="regla-falsa"),
    path("metodos-numericos/regla-falsa/grafica/", explorar_funcion, name="regla-falsa-grafica"),
    path("", views.inicio, name="inicio"),
    path("areas/<slug:area>/", views.area, name="area"),
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
    path("matrices/determinantes/", views.determinantes, name="determinantes"),
    path("bases/conversion/", views.conversion_bases, name="conversion-bases"),
    path("romanos/conversion/", views.conversion_romanos, name="conversion-romanos"),
    # Solo la app de escritorio: tema y formato numérico entre aperturas (404 en la web).
    path("preferencias/", views.guardar_preferencia, name="preferencias"),
    # Solo la app de escritorio: buscar, descargar e instalar actualizaciones (404 en la web).
    path("actualizaciones/", views.actualizaciones, name="actualizaciones"),
    path("actualizaciones/estado/", views.estado_actualizacion, name="actualizaciones-estado"),
    path("actualizaciones/<slug:accion>/", views.accion_actualizacion, name="actualizaciones-accion"),
]
