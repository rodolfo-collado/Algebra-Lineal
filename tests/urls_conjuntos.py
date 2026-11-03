"""Solo pruebas: conserva cobertura del editor sin habilitarlo en la aplicación."""

from django.urls import include, path
from frontend.web.calculadora.urls import urlpatterns as publicas
from frontend.web.calculadora.views_conjuntos import relaciones_conjuntos


urlpatterns = [path("", include(([
    path("conjuntos/relaciones/", relaciones_conjuntos, name="relaciones-conjuntos"),
    *publicas[1:],
], "calculadora"), namespace="calculadora"))]
