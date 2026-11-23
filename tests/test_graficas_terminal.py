"""La vista gráfica conserva la escala y distingue cruces de discontinuidades."""

import os
import unittest

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")
django.setup()

from frontend.terminal.graficas import (
    Cruce, Curva, _detalle, _marcas_eje, detectar_cruces, pintar_imagen, pintar_texto, preparar_vista,
)
from frontend.terminal.raices import curva


_COLORES = {
    "fondo": "#181824", "texto": "#d9d5eb", "curva": "#8edeea",
    "guia": "#c7a5f2", "acento": "#a7dea8", "ejes": "#9c93b6", "rejilla": "#34334b",
}


class GraficasTerminal(unittest.TestCase):
    def test_extension_a_o_b_no_oculta_candidatos_en_vista_previa(self):
        grafica = curva("biseccion", {"funcion": "x^3+x^2-12", "a": "12", "b": "13"})
        self.assertEqual([(m.etiqueta, m.x, m.y) for m in grafica.marcas],
                         [("a", 12, 1860), ("b", 13, 2354)])
        candidatos = detectar_cruces(grafica)
        self.assertEqual(len(candidatos), 1)
        a, b = candidatos[0].intervalo
        self.assertLess(a ** 3 + a ** 2 - 12, 0)
        self.assertGreater(b ** 3 + b ** 2 - 12, 0)

    def test_un_cambio_de_signo_a_traves_de_un_hueco_no_se_marca(self):
        grafica = curva("biseccion", {"funcion": "1/x"})
        self.assertIn(None, grafica.y)
        self.assertEqual(detectar_cruces(grafica), ())

    def test_distingue_corte_tangente_de_cambio_de_signo(self):
        self.assertEqual(detectar_cruces(Curva("f(x)=x²", (-1., 0., 1.), (1., 0., 1.))),
                         (Cruce(0.),))
        self.assertEqual(detectar_cruces(Curva("f(x)=x", (-1., 0., 1.), (-1., 0., 1.))),
                         (Cruce(0., (-1., 1.)),))

    def test_etiquetas_en_unidades_del_ejercicio_en_ambos_renderizadores(self):
        grafica = curva("biseccion", {"funcion": "x^2 - 2", "a": "1", "b": "2"})
        vista = preparar_vista(grafica, 0)
        _, etiquetas = _marcas_eje(vista.xlim, vista.escalas[0], 5, ",")
        self.assertIn("1,25", etiquetas)
        texto = pintar_texto(vista, 72, 14, _COLORES, ",").plain
        self.assertIn("f(x)", texto)
        self.assertIn("1,25", texto)
        self.assertIn("a = 1 · f = -1", _detalle(vista, 0, ",", _COLORES).plain)
        imagen = pintar_imagen(vista, 72, 14, _COLORES, ",")
        self.assertEqual(imagen.size, (720, 280))
        self.assertGreater(len(imagen.getcolors(10_000)), 20)
