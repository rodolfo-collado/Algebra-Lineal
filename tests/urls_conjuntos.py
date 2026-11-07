"""Solo pruebas: conserva cobertura del editor sin habilitarlo en la aplicación."""

from django.urls import include, path
from frontend.web.calculadora.urls import urlpatterns as publicas
from frontend.web.calculadora.views_conjuntos import relaciones_conjuntos, cardinalidades_conjuntos


urlpatterns = [path("", include(([
    path("conjuntos/relaciones/", relaciones_conjuntos, name="relaciones-conjuntos"),
    path('conjuntos/cardinalidad/', cardinalidades_conjuntos, name='cardinalidades-conjuntos'),
    *publicas[1:],
], "calculadora"), namespace="calculadora"))]
