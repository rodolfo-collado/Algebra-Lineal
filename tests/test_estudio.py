"""Contratos de Estudio: áreas con explorador, canales del inicio, mesa de trabajo,
historial real, estilo independiente del tema y sonido opcional.

Comprueban HTML, rutas y recursos estáticos; el comportamiento en un navegador real
(cursor, teclado, transiciones) se revisa a mano, ver docs/pruebas.md.
"""

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "frontend.web.algebra_web.settings")

import django

django.setup()

from django.test import SimpleTestCase
from django.utils.html import escape

from frontend.web.calculadora import catalogo, preferencias
from tests.test_navegacion import Documento, disponibles

APP = Path(__file__).resolve().parents[1] / "frontend" / "web" / "calculadora"
STATIC = APP / "static" / "calculadora"


def areas_disponibles():
    return [area for area in catalogo.AREAS if area.disponible]


class PruebasCatalogoEstudio(SimpleTestCase):
    def test_cada_area_y_categoria_tiene_su_notacion(self):
        for elemento in (*catalogo.AREAS, *catalogo.CATEGORIAS):
            with self.subTest(elemento=elemento.id):
                self.assertTrue(elemento.chip.strip())

    def test_cada_herramienta_disponible_explica_que_permite_y_una_curiosidad(self):
        for herramienta in disponibles():
            with self.subTest(herramienta=herramienta.id):
                self.assertEqual(len(herramienta.puntos), 2)
                self.assertTrue(herramienta.curiosidad.endswith("."))

    def test_las_anclas_llevan_al_explorador_del_area(self):
        self.assertEqual(catalogo.ALGEBRA_LINEAL.ancla, "/areas/algebra-lineal/")
        self.assertEqual(catalogo.MATRICES.ancla, "/areas/algebra-lineal/#matrices")
        self.assertEqual(catalogo.RAICES.ancla, "/areas/metodos-numericos/#raices")

    def test_hermanas_agrupa_las_disponibles_del_area(self):
        grupos = catalogo.hermanas(catalogo.DETERMINANTES)
        self.assertEqual([c for c, _ in grupos], [catalogo.VECTORES, catalogo.MATRICES])
        self.assertIn(catalogo.DETERMINANTES, dict(grupos)[catalogo.MATRICES])
        self.assertEqual(catalogo.hermanas(catalogo.BISECCION), ((catalogo.RAICES, (catalogo.BISECCION,)),))


class PruebasExploradorDeArea(SimpleTestCase):
    def test_cada_area_disponible_tiene_explorador_con_todas_sus_herramientas(self):
        for area in areas_disponibles():
            with self.subTest(area=area.id):
                respuesta = self.client.get(area.ruta)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, f"<title>{area.nombre} · PyGebra</title>", html=True)
                self.assertContains(respuesta, f'data-explorador="{area.id}"')
                documento = Documento(respuesta)
                indice = {a["href"] for a in documento.enlaces_en(f"Herramientas de {area.nombre}")}
                propias = {h.ruta for h in disponibles() if h.area == area}
                self.assertEqual(indice, propias)
                # Las anclas de las migas existen: un id por categoría.
                for categoria in catalogo.CATEGORIAS:
                    if categoria.area == area and categoria.disponible:
                        self.assertIn(categoria.id, documento.ids)

    def test_sin_javascript_el_panel_muestra_la_primera_y_el_resto_espera(self):
        html = self.client.get("/areas/algebra-lineal/").content.decode("utf-8")
        cuerpos = re.findall(r'<div class="destacado-cuerpo" data-id="([^"]+)"[^>]*?( hidden)?>', html)
        self.assertEqual(cuerpos[0], ("operaciones-vectores", ""))
        self.assertTrue(all(oculto for _, oculto in cuerpos[1:]))
        self.assertEqual(len(cuerpos), sum(1 for h in disponibles() if h.area == catalogo.ALGEBRA_LINEAL))
        # Abrir es siempre un enlace real a la herramienta.
        self.assertIn('href="/matrices/determinantes/">Abrir Determinantes', html)

    def test_el_panel_da_contexto_del_tema_sin_repetir_la_herramienta(self):
        for area in areas_disponibles():
            html = self.client.get(area.ruta).content.decode("utf-8")
            cuerpos = dict(re.findall(r'<div class="destacado-cuerpo" data-id="([^"]+)".*?>(.*?)<a class="btn', html, re.S))
            for herramienta in disponibles():
                if herramienta.area != area:
                    continue
                with self.subTest(herramienta=herramienta.id):
                    cuerpo = cuerpos[herramienta.id]
                    self.assertIn(f'<p class="destacado-contexto">{escape(herramienta.categoria.descripcion)}</p>', cuerpo)
                    varias = len(catalogo.herramientas_de(herramienta.categoria)) > 1
                    self.assertEqual("destacado-lema" in cuerpo, varias)
                    # Fuera del panel la descripción sigue accesible desde el índice.
                    self.assertIn(f'id="lema-{herramienta.id}" hidden>{escape(herramienta.descripcion)}', html)

    def test_areas_proximas_o_inexistentes_no_tienen_pagina(self):
        for ruta in ("/areas/conjuntos/", "/areas/calculo/", "/areas/inexistente/"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 404)
        self.assertEqual(self.client.post("/areas/algebra-lineal/").status_code, 405)

    def test_migas_de_area_y_de_herramienta(self):
        area = Documento(self.client.get("/areas/sistemas-numericos/"))
        self.assertEqual([a["href"] for a in area.enlaces_en("Ruta de navegación")], ["/"])
        herramienta = Documento(self.client.get(catalogo.BISECCION.ruta))
        self.assertEqual([a["href"] for a in herramienta.enlaces_en("Ruta de navegación")],
                         ["/", "/areas/metodos-numericos/", "/areas/metodos-numericos/#raices"])


class PruebasCanalesDelInicio(SimpleTestCase):
    def test_un_canal_por_area_y_solo_las_disponibles_enlazan(self):
        respuesta = self.client.get("/")
        html = respuesta.content.decode("utf-8")
        canales = re.findall(r'<li class="canal( es-pronto)?" id="([^"]+)" data-grupo', html)
        self.assertEqual([id_ for _, id_ in canales], [area.id for area in catalogo.AREAS])
        for pronto, id_ in canales:
            area = next(a for a in catalogo.AREAS if a.id == id_)
            with self.subTest(area=id_):
                self.assertEqual(bool(pronto), not area.disponible)
                self.assertEqual(f'href="{area.ruta}"' in html, area.disponible)

    def test_la_bienvenida_presenta_el_proposito_en_ambos_estilos(self):
        html = self.client.get("/").content.decode("utf-8")
        self.assertIn('<p class="home-lead">Aprende resolviendo</p>', html)
        self.assertIn('<p class="home-proposito">Resuelve ejercicios de matemáticas', html)
        self.assertNotIn("Pasa y ponte", html)

    def test_el_buscador_del_inicio_conserva_todo_el_catalogo(self):
        # Cada herramienta, también las próximas, figura en el cajón y en su canal.
        documento = Documento(self.client.get("/"))
        for herramienta in catalogo.HERRAMIENTAS:
            self.assertEqual(documento.indices.count(herramienta.indice), 2)

    def test_bisección_forma_parte_del_recorrido(self):
        inicio = self.client.get("/")
        self.assertContains(inicio, 'href="/areas/metodos-numericos/"')
        area = self.client.get("/areas/metodos-numericos/")
        self.assertContains(area, f'href="{catalogo.BISECCION.ruta}"')
        self.assertContains(area, "Gráfica interactiva del intervalo")


class PruebasMesaDeTrabajo(SimpleTestCase):
    def test_hermanas_solo_si_hay_a_donde_moverse_y_la_actual_marcada(self):
        for herramienta in disponibles():
            with self.subTest(herramienta=herramienta.id):
                documento = Documento(self.client.get(herramienta.ruta))
                rail = documento.enlaces_en(f"Herramientas de {herramienta.area.nombre}")
                propias = [h for h in disponibles() if h.area == herramienta.area]
                if len(propias) > 1:
                    self.assertEqual({a["href"] for a in rail}, {h.ruta for h in propias})
                    self.assertEqual([a["href"] for a in rail if a.get("aria-current") == "page"], [herramienta.ruta])
                else:
                    self.assertEqual(rail, [])

    def test_la_nota_para_curiosos_esta_plegada_junto_al_titulo_en_cada_herramienta(self):
        for herramienta in disponibles():
            with self.subTest(herramienta=herramienta.id):
                html = self.client.get(herramienta.ruta).content.decode("utf-8")
                cabecera = re.search(r'<header class="tool-header">.*?</header>', html, re.S).group(0)
                # Un details nativo: funciona sin JavaScript y nace cerrado.
                self.assertIn('<details class="nota">', cabecera)
                self.assertIn("Para curiosos", cabecera)
                self.assertIn(escape(herramienta.curiosidad), cabecera)
                self.assertLess(cabecera.index("tool-title"), cabecera.index("nota"))
                self.assertEqual(html.count('class="nota"'), 1)


class PruebasHistorialReal(SimpleTestCase):
    def test_atras_y_adelante_nacen_ocultos_y_usan_el_historial_del_navegador(self):
        html = self.client.get("/").content.decode("utf-8")
        self.assertRegex(html, r'<div class="historial" role="group" aria-label="Historial" hidden>')
        for boton in ("historial-atras", "historial-adelante"):
            self.assertIn(f'id="{boton}"', html)
        script = (STATIC / "historial.js").read_text(encoding="utf-8")
        for contrato in ("history.back()", "history.forward()", "nav.canGoBack", "nav.canGoForward",
                         '"currententrychange"', '"pageshow"', "grupo.hidden = false"):
            self.assertIn(contrato, script)
        # Sin pila propia: nada reescribe el historial.
        for archivo in ("historial.js", "navigation.js", "explorador.js"):
            texto = (STATIC / archivo).read_text(encoding="utf-8")
            self.assertNotIn("pushState", texto)
            self.assertNotIn("replaceState", texto)

    def test_la_direccion_se_decide_antes_del_primer_pintado(self):
        inicial = (APP / "templates" / "calculadora" / "components" / "tema_inicial.html").read_text(encoding="utf-8")
        for contrato in ("navigation.activation", '"traverse"', 'root.setAttribute("data-dir"',
                         '"data-llegada"', '"pagehide"'):
            self.assertIn(contrato, inicial)


class PruebasEstiloYSonido(SimpleTestCase):
    def test_estilo_independiente_del_tema_y_guardado_como_preferencia(self):
        inicial = (APP / "templates" / "calculadora" / "components" / "tema_inicial.html").read_text(encoding="utf-8")
        self.assertIn('preferencias.leer("pygebra-estilo") === "minimalista" ? "minimalista" : "estudio"', inicial)
        self.assertEqual(preferencias.VALORES["pygebra-estilo"], ("estudio", "minimalista"))
        self.assertEqual(preferencias.VALORES["pygebra-sonido"], ("off", "on"))
        self.assertEqual(preferencias.VALORES["pygebra-volumen"], tuple(str(n) for n in range(10, 101, 10)))
        html = self.client.get("/").content.decode("utf-8")
        # El servidor no decide el estilo: sin JavaScript no hay data-estilo (forma sobria).
        self.assertNotIn("data-estilo=", re.search(r"<html[^>]*>", html).group(0))
        for valor in ("estudio", "minimalista", "off", "on"):
            self.assertIn(f'value="{valor}"', html)

    def test_los_estilos_de_estudio_solo_viven_en_estudio(self):
        css = (STATIC / "styles" / "estudio.css").read_text(encoding="utf-8")
        self.assertIn("[data-estilo=\"estudio\"][data-theme=\"light\"]", css)
        self.assertIn("[data-estilo=\"estudio\"][data-theme=\"dark\"]", css)
        # Las transiciones entre páginas respetan el movimiento reducido.
        self.assertRegex(css, r"@media \(prefers-reduced-motion: no-preference\) \{\s*@view-transition")
        self.assertIn("@media (forced-colors: active)", css)
        entrada = (STATIC / "styles.css").read_text(encoding="utf-8")
        self.assertLess(entrada.index("navegacion.css"), entrada.index("estudio.css"))

    def test_el_ambiente_se_mueve_solo_al_explorar_y_con_movimiento_permitido(self):
        css = re.sub(r"/\*.*?\*/", "", (STATIC / "styles" / "estudio.css").read_text(encoding="utf-8"), flags=re.S)
        movimiento = css.split("@media (prefers-reduced-motion: no-preference)", 1)[1].split("@keyframes", 1)[0]
        # Toda animación (y todo bucle) vive dentro de no-preference; base.css cancela el resto.
        fuera = css.replace(movimiento, "")
        self.assertNotRegex(fuera, r"\banimation\s*:")
        self.assertNotRegex(fuera, r"\binfinite\b")
        # En el explorador y en la mesa de trabajo la habitación se queda quieta.
        self.assertIn(':is([data-vista="area"], [data-vista="herramienta"]) .escena * { animation-play-state: paused !important; }', movimiento)
        base = (STATIC / "styles" / "base.css").read_text(encoding="utf-8").split("@media (prefers-reduced-motion: reduce)", 1)[1]
        self.assertRegex(base, r"animation:\s*none\s*!important")

    def test_el_sonido_es_opcional_local_y_nunca_la_unica_senal(self):
        sonido = (STATIC / "sonido.js").read_text(encoding="utf-8")
        self.assertIn('preferencias.leer("pygebra-sonido") === "on"', sonido)
        self.assertIn("AudioContext", sonido)
        for ausente in ("fetch(", "new Audio(", ".mp3", ".wav", ".ogg", "http"):
            self.assertNotIn(ausente, sonido)
        html = self.client.get("/").content.decode("utf-8")
        self.assertRegex(html, r'id="opciones-toggle" popovertarget="opciones" hidden')

    def test_la_musica_es_voluntaria_local_e_independiente_de_los_efectos(self):
        musica = (STATIC / "musica.js").read_text(encoding="utf-8")
        piezas = (STATIC / "musica_piezas.js").read_text(encoding="utf-8")
        # Partituras escritas: Math.random no decide ninguna nota.
        for ausente in ("fetch(", "new Audio(", ".mp3", ".wav", ".ogg", "http", "localStorage", "Math.random"):
            self.assertNotIn(ausente, musica)
            self.assertNotIn(ausente, piezas)
        # Cada visita empieza en silencio: encendida solo durante la sesión, nunca como preferencia.
        self.assertIn('sessionStorage.getItem(SESION) === "on"', musica)
        self.assertIn("let deseada = false", musica)
        self.assertNotIn("pygebra-musica", set(preferencias.VALORES))
        self.assertEqual(preferencias.VALORES["pygebra-musica-volumen"], preferencias.VALORES["pygebra-volumen"])
        # Lo elegido se recuerda: las piezas de la lista blanca son las que existen.
        self.assertEqual(preferencias.VALORES["pygebra-musica-pieza"],
                         ("continua", *re.findall(r'^ +id: "(\w+)",$', piezas, re.M)))
        # Calla con la ventana oculta y no gasta en silencio.
        for contrato in ('"visibilitychange"', "document.hidden", "c.suspend()"):
            self.assertIn(contrato, musica)
        html = self.client.get("/").content.decode("utf-8")
        self.assertRegex(html, r'<fieldset class="opciones-grupo" id="musica-grupo" hidden>')
        self.assertIn('id="musica-toggle">Reproducir</button>', html)
        for control in ('id="musica-pieza"', 'id="musica-anterior"', 'id="musica-siguiente"', 'id="musica-volumen"'):
            self.assertIn(control, html)
        self.assertLess(html.index("calculadora/sonido.js"), html.index("calculadora/musica_piezas.js"))
        self.assertLess(html.index("calculadora/musica_piezas.js"), html.index("calculadora/musica.js"))
        self.assertLess(html.index("calculadora/musica.js"), html.index("calculadora/opciones.js"))

    def test_la_escena_es_decorativa_y_sus_ids_no_chocan(self):
        for ruta in ("/", "/areas/algebra-lineal/", catalogo.BISECCION.ruta):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertContains(respuesta, '<div class="escena" aria-hidden="true">')
                ids = Documento(respuesta).ids
                self.assertEqual(len(ids), len(set(ids)))
                for enlace in Documento(respuesta).enlaces:
                    self.assertFalse(urlsplit(enlace[1]["href"]).netloc)
