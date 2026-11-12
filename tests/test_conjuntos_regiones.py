"""La edición por regiones escribe conjuntos; el Venn se vuelve a calcular desde ellos."""

import re
from urllib.parse import parse_qs, urlencode, urlsplit

from django.test import SimpleTestCase
from fractions import Fraction

from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.modelo import Conjunto, presentar
from backend.conjuntos.parser import analizar_expresion
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.regiones import construir_venn, conjuntos_desde_regiones
from frontend.web.calculadora.forms_conjuntos import ConjuntosForm
from tests.test_conjuntos_presentacion import CARDINALIDAD, TRES, contrato, editor
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
        self.assertRegex(r.content.decode(), r'name="venn_region_7"[^>]*>\s*5</textarea>')
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
        # El diagrama vuelve a leer las definiciones aplicadas: lo compartido sigue en su intersección.
        self.assertRegex(r.content.decode(), r'name="venn_region_3"[^>]*>\s*2</textarea>')
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


class DiagramaSincronizadoTests(SimpleTestCase):
    """Conjuntos, diagrama y tarjetas son vistas del mismo modelo; el último lado editado manda."""

    def test_leer_region_acepta_lista_suelta_y_conjunto(self):
        from frontend.web.calculadora.forms_conjuntos import leer_region
        for texto, esperado in (("1, 2", "{1, 2}"), ("{1, 2}", "{1, 2}"), ("", "∅"), ('"a"', '{"a"}'),
                                ("{1}, {2}", "{{1}, {2}}"), ("1/2, par(1, 2)", "{1/2, par(1, 2)}")):
            with self.subTest(texto=texto):
                self.assertEqual(presentar(leer_region(texto, Presupuesto())), esperado)
        with self.assertRaises(ValueError):
            leer_region("{1,", Presupuesto())

    def test_escribir_y_leer_una_region_conserva_sus_elementos(self):
        # Ida y vuelta: lo que el diagrama escribe en una región se relee igual, también al añadir
        # elementos detrás («5» + «, 11»), que era ambiguo cuando la región mostraba «{5}».
        from frontend.web.calculadora.forms_conjuntos import escribir_region, leer_region
        for texto in ("∅", "{1}", "{1, 3}", "{{1}}", "{{1}, 2}", "{∅}", "{∅, 1}", '{"a"}', "{par(1, {2})}",
                      "{intervalo(0, 1, cerrado, cerrado)}"):
            region = analizar_literal(texto)
            with self.subTest(region=texto):
                self.assertEqual(leer_region(escribir_region(list(region.elementos)), Presupuesto()), region)
        self.assertEqual(escribir_region([Fraction(1), Fraction(3)]), "1, 3")
        self.assertEqual(escribir_region([analizar_literal("{1}")]), "{{1}}")
        self.assertEqual(presentar(leer_region(escribir_region([Fraction(5)]) + ", 11", Presupuesto())), "{5, 11}")

    def test_diagrama_siempre_lee_el_modelo_y_ofrece_exterior(self):
        r = self.client.get(RUTA)
        self.assertContains(r, 'name="venn_region_1"')
        self.assertContains(r, 'placeholder="?"')  # exterior aún desconocido: U no existe
        self.assertNotContains(r, 'class="tarjetas"')
        r = self.client.get(RUTA + "?ejemplo=venn")
        self.assertRegex(r.content.decode(), r'name="venn_region_0"[^>]*>\s*8, 10</textarea>')
        self.assertContains(r, 'name="base_nombres" value="A, B, C"')
        # Con intervalos no hay conjuntos finitos que dibujar: se explica, sin inventar regiones.
        r = self.client.get(RUTA + "?ejemplo=intervalos")
        self.assertNotContains(r, 'name="venn_region_1"')
        self.assertContains(r, "recta real")

    def test_calcular_aplica_antes_el_diagrama_editado(self):
        campos = editor([("A", "{1}"), ("B", "{2}")], "A ∪ B", base_nombres="A, B", base_universo="U",
                        venn_fuente="regiones", venn_region_0="", venn_region_1="1, 7", venn_region_2="2",
                        venn_region_3="5")
        r = self.client.post(RUTA, campos)
        self.assertContains(r, 'data-respuesta-relacion>{1, 2, 5, 7}</p>', html=False)
        self.assertRegex(r.content.decode(), r'name="contenido_0"[^>]*>\s*\{1, 5, 7\}</textarea>')
        # Sin exterior escrito no se crea un universo.
        self.assertNotContains(r, 'name="nombre_2"')
        # Si mandan los conjuntos, el borrador del diagrama se ignora y se vuelve a leer.
        r = self.client.post(RUTA, {**campos, "venn_fuente": ""})
        self.assertContains(r, 'data-respuesta-relacion>{1, 2}</p>', html=False)

    def test_exterior_crea_universo_y_cambiar_nombres_descarta_regiones(self):
        campos = editor([], "", accion="aplicar_regiones", base_nombres="A, B", base_universo="U",
                        venn_region_0="9", venn_region_1="1", venn_region_2="", venn_region_3="")
        form = ConjuntosForm(campos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(dict(form.filas), {"A": "{1}", "B": "∅", "U": "{1, 9}"})
        r = self.client.post(RUTA, editor(TRES, "", accion="editar_regiones", venn_nombres="A, B",
                                          base_nombres="A, B, C", base_universo="U",
                                          **{f"venn_region_{m}": "" for m in range(8)}))
        self.assertNotContains(r, "campos ajenos")
        self.assertNotContains(r, 'name="venn_region_7"')

    def test_tarjetas_salen_del_modelo(self):
        from frontend.web.calculadora.servicios_conjuntos import panorama_web
        regiones = {0: (Fraction(9),), 1: (Fraction(1),), 2: (Fraction(3),), 3: (Fraction(2),)}
        p = panorama_web(("A", "B"), "U", regiones)
        valores = {t["clave"]: (t["texto"], t["cantidad"]) for t in p["operaciones"]}
        self.assertEqual(valores["union"], ("{1, 2, 3}", 3))
        self.assertEqual(valores["simetrica"], ("{1, 3}", 2))
        self.assertEqual(valores["complemento_union"], ("{9}", 1))
        self.assertEqual(p["inclusion_exclusion"]["valores"], "3 = 2 + 2 − 1")
        self.assertEqual(p["relaciones"][0][0], "A ∩ B ≠ ∅")
        # Solo cantidades: ninguna tarjeta escribe elementos.
        p = panorama_web(("A", "B", "C"), None, {m: m for m in range(8)}, cantidades=True)
        self.assertTrue(all(t["texto"].isdigit() for t in p["operaciones"]))
        self.assertEqual(p["inclusion_exclusion"]["valores"], "28 = 16 + 18 + 22 − 10 − 12 − 13 + 7")
        incluido = panorama_web(("A", "B"), None, {1: (), 2: (Fraction(3),), 3: (Fraction(2),)})
        self.assertEqual(incluido["relaciones"][0][0], "A ⊂ B")

    def test_ver_pasos_de_una_tarjeta(self):
        base = editor(TRES, "A", base_nombres="A, B, C", base_universo="U")
        r = self.client.post(RUTA, {**base, "tarjeta": "solo_0"})
        self.assertContains(r, 'data-respuesta-relacion>{1, 3}</p>', html=False)
        self.assertContains(r, "A ∖ (B ∪ C)</textarea>")
        self.assertContains(self.client.post(RUTA, {**base, "tarjeta": "eval"}), "no está entre las tarjetas")
        # Renombrar A sin guardar y pedir los pasos usa ya el nombre nuevo.
        r = self.client.post(RUTA, {**base, "nombre_1": "P", "tarjeta": "union"})
        self.assertContains(r, "P ∪ B ∪ C</textarea>")
        self.assertContains(r, 'data-respuesta-relacion>{1, 2, 3, 4, 5, 6, 7, 9}</p>', html=False)

    def test_cantidades_reciben_solo_enteros(self):
        r = self.client.get(RUTA + "?ejemplo=venn")
        self.assertContains(r, "numero=3&amp;region_1=2&amp;region_2=1&amp;region_3=1&amp;region_4=1&amp;region_5=1&amp;region_6=1&amp;region_7=1&amp;universo=10")
        r = self.client.get("/conjuntos/cardinalidad/?numero=2&region_1=5&region_2=x&region_3=" + "9" * 101 + "&universo=7")
        self.assertContains(r, 'name="region_1" value="5"')
        self.assertNotContains(r, 'name="region_2" value="x"')
        self.assertNotContains(r, "9" * 101)
        self.assertContains(r, 'name="universo" value="7"')


class UnVennYContextoTests(SimpleTestCase):
    """Tras Calcular hay un solo Venn, y Cantidades devuelve a Elementos el editor tal como estaba."""

    def test_el_resultado_se_sombrea_en_el_diagrama_editable(self):
        r = self.client.post(RUTA, editor(TRES, "(A ∪ B) ∖ C", venn_universo="U"))
        venn = contrato(r)["venn"]
        self.assertEqual(venn["nombres"], ["A", "B", "C"])
        self.assertEqual([x["mascara"] for x in venn["regiones"] if x["seleccionada"]], [1, 2, 3])
        self.assertContains(r, "data-venn-en-diagrama")
        self.assertNotContains(r, "data-venn></div>")
        self.assertContains(r, '<span class="conjuntos-si">Sí</span>', count=3)
        self.assertRegex(r.content.decode(), r'name="venn_region_1"[^>]*>\s*1, 3</textarea>')
        # Una expresión de dos de los tres conjuntos se sombrea igual sobre los tres.
        venn = contrato(self.client.post(RUTA, editor(TRES, "A ∖ B")))["venn"]
        self.assertEqual(([x["mascara"] for x in venn["regiones"] if x["seleccionada"]], len(venn["regiones"])), ([1, 5], 8))

    def test_relacion_no_repite_el_diagrama_y_otros_conjuntos_conservan_el_suyo(self):
        r = self.client.post(RUTA, editor(TRES, "A ⊆ B", venn_nombres="A, B, C"))
        self.assertIn("venn", contrato(r))
        self.assertNotContains(r, 'class="panel conjuntos-venn"')
        r = self.client.post(RUTA, editor(TRES + [("D", "{1, 20}")], "A ∪ D"))
        self.assertEqual(contrato(r)["venn"]["nombres"], ["A", "D"])
        self.assertContains(r, "data-venn></div>")
        self.assertNotContains(r, "data-venn-en-diagrama")

    def test_cardinalidad_por_regiones_sombrea_sus_casillas(self):
        campos = {"numero": "2", "modo": "regiones", "region_1": "5", "region_2": "3", "region_3": "2",
                  "expresion": "A", "accion": "calcular"}
        r = self.client.post(CARDINALIDAD, campos)
        self.assertContains(r, "data-venn-en-diagrama")
        self.assertNotContains(r, "data-venn></div>")
        r = self.client.post(CARDINALIDAD, {**campos, "modo": "intersecciones", "region_1": "7"})
        self.assertContains(r, "data-venn></div>")

    def test_cantidades_devuelve_el_editor_intacto(self):
        r = self.client.get(RUTA + "?ejemplo=venn")
        enlace = re.search(r'href="(/conjuntos/cardinalidad/\?[^"]*)"', r.content.decode())[1].replace("&amp;", "&")
        ida = parse_qs(urlsplit(enlace).query)
        self.assertEqual(ida["region_1"], ["2"])
        self.assertNotIn("contenido_1", ida)  # los elementos no viajan como datos de Cantidades
        cantidades = self.client.get(enlace)
        self.assertNotContains(cantidades, "{1, 2, 3, 4, 5}")
        vuelta = re.search(r'class="venn-modo-opcion" href="([^"]*)"', cantidades.content.decode())[1].replace("&amp;", "&")
        # Contar no pierde el camino de vuelta.
        datos = {"numero": "3", "modo": "regiones", "accion": "calcular", "expresion": "A",
                 "volver": ida["volver"][0], **{f"region_{m}": "1" for m in range(1, 8)}}
        tras_contar = self.client.post(CARDINALIDAD, datos)
        self.assertEqual(re.search(r'class="venn-modo-opcion" href="([^"]*)"', tras_contar.content.decode())[1].replace("&amp;", "&"), vuelta)
        r = self.client.get(vuelta)
        self.assertContains(r, 'name="nombre_3" value="C"')
        self.assertContains(r, "{1, 2, 3, 4, 5}</textarea>")
        self.assertContains(r, "(A ∪ B) ∖ C</textarea>")
        self.assertContains(r, 'name="venn_universo" value="U"')
        self.assertRegex(r.content.decode(), r'name="venn_region_1"[^>]*>\s*1, 3</textarea>')

    def test_volver_solo_admite_campos_del_editor(self):
        for volver in ("cantidad=1&nombre_0=A&evil=1", "nombre_0=A", "http://otro.example/"):
            with self.subTest(volver=volver):
                r = self.client.get(CARDINALIDAD + "?" + urlencode({"volver": volver}))
                self.assertContains(r, 'class="venn-modo-opcion" href="/conjuntos/relaciones/"')
        r = self.client.get(RUTA + "?" + urlencode({"cantidad": "999", "nombre_0": "A", "contenido_0": "{1"}))
        self.assertContains(r, 'name="cantidad" value="50"')
        self.assertContains(r, "{1</textarea>")
