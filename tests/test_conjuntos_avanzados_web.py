import json
import re

from django.test import SimpleTestCase
from tests.test_conjuntos_web import datos, RUTA


def contrato(respuesta):
    texto = respuesta.content.decode()
    return json.loads(re.search(r'<script id="conjuntos-resultado-datos"[^>]*>(.*?)</script>',texto,re.S)[1])


class AvanzadosWebTests(SimpleTestCase):
    def test_pares_potencia_y_recta_tipados(self):
        respuesta = self.client.post(RUTA,datos(expresion='{1} × {2}'))
        par = contrato(respuesta)['valor']['elementos'][0]
        self.assertEqual(par['tipo'],'par')
        self.assertEqual(par['segundo']['numerador'],'2')
        self.assertContains(self.client.post(RUTA,datos(expresion='|potencia(A)|')), 'data-respuesta-relacion>4</p>')
        respuesta = self.client.post(RUTA,datos(expresion='intervalo(-inf, 1/2, abierto, cerrado)',punto='0.5'))
        d = contrato(respuesta)
        self.assertEqual(d['valor']['tipo'],'recta')
        self.assertEqual(d['valor']['intervalos'][0]['superior']['denominador'],'2')
        self.assertIs(d['recta']['pertenece'],True)
        self.assertContains(respuesta,'data-recta')
        self.assertContains(respuesta,'pertenece al resultado')
        for punto in ('abc', '{1}', '1 ∪'):
            with self.subTest(punto=punto):
                respuesta = self.client.post(RUTA,datos(expresion='intervalo(0, 1, abierto, cerrado)',punto=punto))
                self.assertContains(respuesta,'Escribe un número exacto')
                self.assertContains(respuesta,'data-recta')

    def test_venn_incluye_regiones_vacias_y_elementos_completos(self):
        respuesta = self.client.post(RUTA,datos(expresion='A ∩ B',venn_nombres='A, B'))
        regiones = contrato(respuesta)['venn']['regiones']
        self.assertEqual(len(regiones),4)
        self.assertEqual(regiones[3]['etiquetas'],['2'])
        self.assertTrue(regiones[3]['seleccionada'])
        self.assertContains(respuesta,'data-venn')
        for extra in ({'venn_nombres':'A,A'},{'venn_nombres':'A,B','venn_universo':'Z'}):
            with self.subTest(extra=extra):
                self.assertNotContains(self.client.post(RUTA,datos(**extra)), 'id="resultado"')
        for expresion in ('potencia(A)', '|A ∪ B|', 'A ∈ B'):
            respuesta = self.client.post(RUTA, datos(venn_nombres='A,B', expresion=expresion))
            venn = contrato(respuesta)['venn']
            self.assertFalse(venn['resalta'])
            self.assertFalse(any(r['seleccionada'] for r in venn['regiones']))
            self.assertNotContains(respuesta, '<th scope="col">En el resultado</th>')
        # Un punto escrito para una recta anterior no se aplica a otros resultados.
        self.assertNotIn('recta', contrato(self.client.post(RUTA,datos(punto='1',expresion='A'))))

    def test_cardinalidad_sin_javascript_y_ajustes(self):
        ruta = '/conjuntos/cardinalidad/'
        campos = {'numero':'2','modo':'intersecciones','region_1':'10','region_2':'8','region_3':'3','universo':'20','expresion':'∁(A,U)'}
        respuesta = self.client.post(ruta,campos)
        self.assertContains(respuesta,'data-cardinalidad>10</span>')
        d = contrato(respuesta)
        self.assertEqual(d['union'],'15')
        self.assertEqual(d['venn']['regiones'][0]['cantidad'],'5')
        self.assertEqual(d['pasos'][-2]['regla'],'inclusion_exclusion')
        for cambios in ({'region_3':'11'},{'universo':'14'},{'region_1':'-1'},
                         {'region_1':'0.5'},{'region_1':['1','2']},{'intruso':'x'},
                         {'numero':'9'},{'modo':'otro'},{'accion':'otro'},{'region_1':''}):
            with self.subTest(cambios=cambios):
                self.assertNotContains(self.client.post(ruta,{**campos,**cambios}),'data-cardinalidad')
        respuesta = self.client.post(ruta,{**campos,'numero':'3','accion':'ajustar'})
        self.assertContains(respuesta,'name="region_7"')
        respuesta = self.client.post(ruta,{**campos,'region_7':'1','accion':'ajustar'})
        self.assertNotContains(respuesta,'name="region_7"')
        self.assertEqual(self.client.put(ruta).status_code,405)
