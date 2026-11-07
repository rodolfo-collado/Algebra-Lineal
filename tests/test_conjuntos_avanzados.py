from fractions import Fraction
import unittest
from unittest.mock import patch

from backend.conjuntos.evaluador import evaluar_expresion
from backend.conjuntos.literales import analizar_literal
from backend.conjuntos.modelo import Conjunto, Par
from backend.conjuntos.parser import analizar_expresion, renombrar_referencias
from backend.conjuntos.modelo import presentar
from backend.conjuntos.presupuesto import Presupuesto
from backend.conjuntos.intervalos import Intervalo, Recta, contiene, operar_rectas
from backend.conjuntos.regiones import construir_venn
from backend.conjuntos.cardinalidades import resolver_cardinalidades


def calcular(texto, entorno=None, presupuesto=None):
    presupuesto = presupuesto or Presupuesto()
    return evaluar_expresion(analizar_expresion(texto, presupuesto=presupuesto), entorno or {}, presupuesto=presupuesto)


class GeneracionTests(unittest.TestCase):
    def test_potencia_vacio_anidacion_y_relaciones(self):
        self.assertEqual(calcular('potencia(∅)').valor, analizar_literal('{∅}'))
        self.assertEqual(calcular('potencia({1,2,2})').valor, analizar_literal('{∅,{1},{2},{1,2}}'))
        self.assertIs(calcular('{∅} ∈ potencia({∅})').valor, True)
        self.assertEqual(calcular('|potencia({1,{1}})|').valor, Fraction(4))

    def test_pares_y_productos(self):
        self.assertIs(calcular('par(1,2) ≠ par(2,1)').valor, True)
        self.assertIs(calcular('par(1,2) ∈ {1} × {2}').valor, True)
        with self.assertRaises(ValueError):
            calcular('par(1,2) = {1,2}')
        self.assertEqual(calcular('∅ × {1}').valor, Conjunto())
        self.assertEqual(calcular('|{1,1.0,{1}} × {"1",2}|').valor, Fraction(4))
        self.assertEqual(calcular('{1} × {2} × {3}').valor,
                         Conjunto(frozenset([Par(Par(Fraction(1), Fraction(2)), Fraction(3))])))
        self.assertEqual(calcular('{1} ∪ {2} × {3}').valor, analizar_literal('{1,par(2,3)}'))

    def test_reserva_antes_de_generar(self):
        a = analizar_literal('{' + ','.join(map(str, range(20))) + '}')
        with patch('backend.conjuntos.generacion.Par', side_effect=AssertionError('Generó antes de reservar')):
            with self.assertRaisesRegex(ValueError, 'presupuesto'):
                calcular('A × A', {'A': a}, Presupuesto(procedimiento=44999))
        with self.assertRaisesRegex(ValueError, 'presupuesto'):
            calcular('potencia(A)', {'A': a})
        for texto in ('potencia(1)', '1 × {}', 'par(1)', '(1,2)', 'potencia({1}, {2})'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                calcular(texto)


class IntervalosTests(unittest.TestCase):
    def test_literales_anidados_y_renombrado_contextual(self):
        texto = '{par(1, {2}), intervalo(-inf, 2, abierto, cerrado)}'
        valor = analizar_literal(texto)
        self.assertEqual(analizar_literal(presentar(valor)),valor)
        self.assertEqual(renombrar_referencias('abierto ∪ intervalo(-inf, inf, abierto, abierto)',
                                              {'abierto':'S','inf':'T'}),
                         'S ∪ intervalo(-inf, inf, abierto, abierto)')
    def test_sintaxis_operaciones_y_relaciones(self):
        a = 'intervalo(0,2,cerrado,cerrado)'
        b = 'intervalo(1,1,cerrado,cerrado)'
        diferencia = calcular(f'{a} ∖ {b}').valor
        self.assertEqual(len(diferencia.intervalos), 2)
        self.assertFalse(contiene(diferencia, Fraction(1)))
        for texto, esperado in ((f'1 ∈ {a}', True), (f'{b} ⊂ {a}', True),
                                ('intervalo(0,0,abierto,cerrado) = ∅', True),
                                ('0 ∈ intervalo(-inf,0,abierto,abierto)', False),
                                ('|intervalo(2,2,cerrado,cerrado)| = 1', True),
                                (f'∁({b},{a}) = {a} ∖ {b}', True)):
            with self.subTest(texto=texto):
                self.assertIs(calcular(texto).valor, esperado)
        for texto in ('intervalo(2,1,cerrado,cerrado)', 'intervalo(-inf,1,cerrado,cerrado)',
                      'intervalo(0,-inf,abierto,abierto)', 'intervalo("0",1,abierto,abierto)',
                      'intervalo(0,1,mal,abierto)', '|intervalo(0,1,abierto,abierto)|',
                      f'{a} ∪ {{1}}', f'∁({a},{b})', 'potencia(intervalo(0,1,abierto,abierto))'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                calcular(texto)

    def test_tabla_exhaustiva_extremos_y_contactos(self):
        intervalos = []
        for inferior in (None, Fraction(-1), Fraction(0), Fraction(1)):
            for superior in (Fraction(-1), Fraction(0), Fraction(1), None):
                if inferior is not None and superior is not None and inferior > superior:
                    continue
                for ci in (False, True):
                    for cs in (False, True):
                        if (inferior is None and ci) or (superior is None and cs):
                            continue
                        intervalos.append(Recta((Intervalo(inferior, superior, ci, cs),)))
        puntos = [Fraction(i,2) for i in range(-4,5)]
        for a in intervalos:
            for b in intervalos:
                for op in ('∪','∩','∖'):
                    resultado = operar_rectas(op,a,b)
                    for x in puntos:
                        ea, eb = contiene(a,x), contiene(b,x)
                        esperado = (ea or eb) if op == '∪' else ((ea and eb) if op == '∩' else (ea and not eb))
                        self.assertEqual(contiene(resultado,x), esperado, (a,b,op,x))


class RegionesTests(unittest.TestCase):
    def test_venn_tres_conjuntos_todas_las_regiones(self):
        entorno = {nombre: Conjunto(frozenset(Fraction(m) for m in range(8) if m & (1 << i))) for i,nombre in enumerate('ABC')}
        entorno['U'] = Conjunto(frozenset(Fraction(m) for m in range(8)))
        regiones = construir_venn(('A','B','C'), entorno, analizar_expresion('∁(A,U) ∩ B'), universo='U')
        self.assertEqual([r['mascara'] for r in regiones if r['seleccionada']], [2,6])
        for m,r in enumerate(regiones):
            self.assertEqual(r['elementos'], (Fraction(m),))
        vacias = construir_venn(('A','B'), {'A': Conjunto(),'B': Conjunto()}, analizar_expresion('A ∩ B'))
        self.assertTrue(vacias[3]['seleccionada'])
        self.assertFalse(vacias[0]['exterior_conocido'])

    def test_venn_rechaza_referencias_universos_y_operaciones_ajenas(self):
        entorno = {'A':analizar_literal('{1}'),'B':Conjunto(),'U':Conjunto()}
        for nombres,expresion,universo in ((('A','A'),'A',None),(('A','B'),'potencia(A)',None),
                                          (('A','B'),'A ∪ {1}',None),(('A','B'),'A','U'),
                                          (('A','B'),'Z',None)):
            with self.subTest(expresion=expresion), self.assertRaises(ValueError):
                construir_venn(nombres,entorno,analizar_expresion(expresion),universo=universo)

    def test_cardinalidades_intersecciones_inclusion_exclusion(self):
        r = resolver_cardinalidades(('A','B','C'), {1:10,2:9,4:8,3:4,5:3,6:2,7:1}, modo='intersecciones', universo=25, expresion='∁(A,U) ∩ B')
        self.assertEqual(r['union'], 19)
        self.assertEqual(r['regiones'], {0:6,1:4,2:4,3:3,4:4,5:2,6:1,7:1})
        self.assertEqual(r['resultado'], 5)
        vuelta = resolver_cardinalidades(('A','B','C'), {m:r['regiones'][m] for m in range(1,8)}, universo=25, expresion='A ∪ B ∪ C')
        self.assertEqual(vuelta['intersecciones'], r['intersecciones'])
        self.assertEqual(vuelta['resultado'], 19)
        self.assertEqual(r['pasos'][-2]['regla'], 'inclusion_exclusion')

    def test_cardinalidades_errores_y_presupuesto(self):
        for datos,extra in (({1:1,2:1,3:2},{'modo':'intersecciones'}),
                             ({1:-1,2:0,3:0},{}),({1:True,2:0,3:0},{}),
                             ({1:1,2:1,3:1},{'universo':2}),({1:1},{}),
                             ({1:1,2:0,3:0},{'expresion':'∁(A,U)'})):
            with self.subTest(datos=datos,extra=extra), self.assertRaises(ValueError):
                resolver_cardinalidades(('A','B'), datos, **extra)
        with self.assertRaisesRegex(ValueError,'presupuesto'):
            resolver_cardinalidades(('A','B'), {1:0,2:0,3:0}, presupuesto=Presupuesto(calculo=45000))
