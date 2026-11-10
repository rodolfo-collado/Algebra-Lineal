"""La edición por regiones escribe conjuntos; el Venn se vuelve a calcular desde ellos."""

from django.test import SimpleTestCase
from fractions import Fraction

from backend.conjuntos.modelo import Conjunto
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.regiones import construir_venn, conjuntos_desde_regiones
from frontend.web.calculadora.forms_conjuntos import ConjuntosForm
from tests.test_conjuntos_presentacion import TRES, contrato, editor
from tests.test_conjuntos_web import RUTA


class RegionesEditorTests(SimpleTestCase):
    def test_conversion_inversa_conserva_cada_region(self):
        for nombres in (("A", "B"), ("A", "B", "C")):
            for universo in (None, "U"):
                regiones = {m: Conjunto([Fraction(m), f"región {m}"])
                            for m in range(0 if universo else 1, 1 << len(nombres))}
                entorno = conjuntos_desde_regiones(nombres, regiones, universo=universo)
                inversa = construir_venn(nombres, entorno, analizar_expresion(" ∪ ".join(nombres)), universo=universo)
                for region in inversa:
                    if region["exterior_conocido"]:
                        self.assertEqual(Conjunto(region["elementos"]), regiones[region["mascara"]])
        with self.assertRaisesRegex(ValueError, "presupuesto"):
            conjuntos_desde_regiones(("A", "B"), {m: Conjunto() for m in (1, 2, 3)},
                                     presupuesto=Presupuesto(calculo=45000))

    def test_lee_regiones_del_modelo_y_conserva_definiciones(self):
        r = self.client.post(RUTA, editor(TRES, "(A ∪ B) ∖ C", accion="editar_regiones",
                                         venn_nombres="A, B, C", venn_universo="U"))
        self.assertContains(r, 'name="venn_region_7"')
        self.assertContains(r, 'En A, B y C</label>')
        self.assertRegex(r.content.decode(), r'name="venn_region_7"[^>]*>\s*\{5\}</textarea>')
        self.assertNotContains(r, 'id="resultado"')
        self.assertContains(r, 'name="nombre_0" value="U"')

    def test_aplica_dos_conjuntos_y_exterior_sin_javascript(self):
        campos = editor([("S", '{"conservar"}')], "", accion="aplicar_regiones",
                        venn_nombres="A, B", venn_universo="U", venn_region_0="{9}",
                        venn_region_1="{1, {2}}", venn_region_2='{"rojo"}', venn_region_3="{2, 2}")
        form = ConjuntosForm(campos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(dict(form.filas), {"S": '{"conservar"}', "A": "{1, 2, {2}}",
                                           "B": '{2, "rojo"}', "U": '{1, 2, 9, "rojo", {2}}'})
        r = self.client.post(RUTA, campos)
        self.assertContains(r, 'name="nombre_3" value="U"')
        self.assertContains(r, 'A ∪ B</textarea>')
        self.assertNotContains(r, 'name="venn_region_1"')
        calculo = self.client.post(RUTA, editor(form.filas, form.expresion, venn_nombres="A,B", venn_universo="U"))
        self.assertEqual(contrato(calculo)["venn"]["regiones"][3]["etiquetas"], ["2"])

    def test_tres_conjuntos_compartidos_y_vacios(self):
        campos = editor([], "A ∩ B ∩ C", accion="aplicar_regiones", venn_nombres="A,B,C",
                        **{f"venn_region_{m}": "{1/2, par(1, 2)}" if m == 7 else "" for m in range(1, 8)})
        form = ConjuntosForm(campos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.filas), 3)
        self.assertEqual({c for _, c in form.filas}, {"{1/2, par(1, 2)}"})

    def test_rechaza_incoherencias_y_conserva_borrador(self):
        base = editor([], "", accion="aplicar_regiones", venn_nombres="A,B",
                      venn_region_1="{1/2}", venn_region_2="{0.5}", venn_region_3="")
        r = self.client.post(RUTA, base)
        self.assertContains(r, "regiones distintas")
        self.assertContains(r, 'role="alert"')
        self.assertNotContains(r, 'name="nombre_0"')
        for cambios, mensaje in (({"venn_nombres": "A,A"}, "distintos"),
                                  ({"venn_universo": "A"}, "distinto"),
                                  ({"venn_region_1": "intervalo(0,1,cerrado,cerrado)"}, "finito"),
                                  ({"venn_region_1": "{1,}"}, "Se esperaba"),
                                  ({"venn_region_7": "{3}"}, "campos ajenos"),
                                  ({"venn_region_1": ["{1}", "{2}"]}, "repetidos")):
            with self.subTest(cambios=cambios):
                self.assertContains(self.client.post(RUTA, {**base, **cambios}), mensaje)

    def test_azar_genera_regiones_disjuntas_sin_aplicar(self):
        r = self.client.post(RUTA, editor([], "", accion="azar_regiones", venn_nombres="A,B,C", venn_universo="U"))
        self.assertContains(r, 'name="venn_region_0"')
        self.assertContains(r, 'name="venn_region_7"')
        self.assertNotContains(r, 'name="nombre_0"')

    def test_menu_y_selector_compactos(self):
        r = self.client.get(RUTA)
        self.assertContains(r, 'data-edicion-abrir="id_definicion"')
        self.assertContains(r, 'data-ejemplos-menu')
        self.assertContains(r, '<select name="plantilla"')
        self.assertNotContains(r, 'id="guia-conjuntos"')
        self.assertNotContains(r, 'class="conjuntos-ejemplo-lista"')

    def test_limites_y_cambios_son_atomicos(self):
        campos = editor([(f"S{i}", "∅") for i in range(50)], "", accion="aplicar_regiones",
                        venn_nombres="A,B", venn_region_1="", venn_region_2="", venn_region_3="")
        f = ConjuntosForm(campos)
        self.assertFalse(f.is_valid())
        self.assertIn("50 conjuntos", str(f.errors))
        self.assertEqual(len(f.filas), 50)
        campos = editor([], "", accion="aplicar_regiones", venn_nombres="A,B",
                        venn_region_1="{" + ",".join("1" for _ in range(901)) + "}", venn_region_2="", venn_region_3="")
        f = ConjuntosForm(campos)
        self.assertFalse(f.is_valid())
        self.assertIn("900 elementos", str(f.errors))
        self.assertEqual(f.filas, [])
