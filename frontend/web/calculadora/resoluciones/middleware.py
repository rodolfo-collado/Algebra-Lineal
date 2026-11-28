"""Guarda y reabre resoluciones alrededor de las vistas, sin modificarlas.

- POST con un resultado válido: se guarda y la página recibe ``resolucion_cuaderno`` (el aviso).
- GET con ``?resolucion=<id>``: la vista arma su página vacía, sin calcular, y aquí se
  reponen el formulario y el resultado guardados. La plantilla es la misma de siempre.

Las particularidades de cada herramienta están en ``registro``; la lógica, en ``servicio``.
"""

import logging

from . import registro, servicio


LOG = logging.getLogger(__name__)


class ResolucionesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, vista, args, kwargs):
        adaptador = registro.adaptador(request.resolver_match)
        if adaptador and request.method == "GET" and "resolucion" in request.GET:
            request.resolucion = abierta = servicio.abrir(request.GET["resolucion"], request.resolver_match)
            if adaptador.por_consulta and abierta.get("datos") is not None:
                # La vista rellena su editor desde la consulta, como al volver de otra página.
                consulta = request.GET.copy()
                consulta.update(abierta["datos"])
                request.GET = consulta
        return None

    def process_template_response(self, request, response):
        adaptador = registro.adaptador(getattr(request, "resolver_match", None))
        contexto = getattr(response, "context_data", None)
        if adaptador is None or contexto is None:
            return response
        if request.method == "POST":
            contexto["resolucion_cuaderno"] = servicio.guardar(request, adaptador, contexto)
            return response
        abierta = getattr(request, "resolucion", None)
        if abierta is None:
            return response
        original = dict(contexto)
        contexto["resolucion_cuaderno"] = servicio.reabrir(abierta, adaptador, contexto)
        try:
            # Se renderiza aquí para que un documento que la plantilla no sepa mostrar no rompa la página.
            response.render()
        except Exception:
            LOG.exception("La resolución %s no se pudo mostrar.", abierta.get("id"))
            response.context_data = original | {"resolucion_cuaderno": {"estado": "danado", "id": abierta.get("id")}}
            response.render()
        return response
