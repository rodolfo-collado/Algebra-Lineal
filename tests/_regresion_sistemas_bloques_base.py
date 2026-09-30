"""Fixtures estáticas capturadas desde el árbol Git original de develop.

Base: 79c04d999775387092771538fc3e668c8da47e2a.
Los racionales son texto exacto y cada paso es (operación, antes, después).
Las partes idénticas entre métodos y el prefijo de pasos se almacenan una sola vez.
Git no se ejecuta ni se importa durante las pruebas.
"""

BASELINE_SHA = '79c04d999775387092771538fc3e668c8da47e2a'

CASOS_BASE = {
    'unica': {
        'matriz': [['1', '1', '3'], ['1', '-1', '1']],
        'texto': 'x1+1+x2=4;x1-x2=1',
        'reescritas': [{'numero': 1, 'original': 'x1+1+x2=4', 'estandar': 'x1 + x2 = 3'}],
        'comun': {
            'columnas_pivote': [1, 2],
            'clasificacion': 'Consistente de solución única',
            'solucion_general': ['x1 = 2', 'x2 = 1'],
            'expresiones_solucion': [{'constante': '2', 'coeficientes': {}}, {'constante': '1', 'coeficientes': {}}],
            'soluciones': ['2', '1'],
            'fila_inconsistente': None,
            'filas_nulas': [],
            'variables_libres': [],
            'justificacion': [],
        },
        'final_html': ('Resultado final Clasificación Consistente de solución única Solución x1 = 2 x2 = 1 Columnas pivote '
         'Columnas pivote: C1, C2 C1 C2 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '1', '3'], ['0', '1', '1']],
            'pasos_sustitucion': [{'variable': 2, 'expresion': '1', 'valor': '1'},
             {'variable': 1, 'expresion': '3 - (1)(1)', 'valor': '2'}],
            'ecuaciones_resultantes': ['x1 + x2 = 3', 'x2 = 1'],
            'solucion_directa': False,
            'sustitucion_web': ['x2 = 1', 'x1 = 3 - (1)(1) = 2'],
            'pasos': [('F2 = F2 - (1)F1', [['1', '1', '3'], ['1', '-1', '1']], [['1', '1', '3'], ['0', '-2', '-2']]),
             ('F2 = (-1/2)F2', [['1', '1', '3'], ['0', '-2', '-2']], [['1', '1', '3'], ['0', '1', '1']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '0', '2'], ['0', '1', '1']],
            'ecuaciones_resultantes': ['x1 = 2', 'x2 = 1'],
            'solucion_directa': True,
            'sustitucion_web': [],
            'pasos_adicionales': [('F1 = F1 - (1)F2', [['1', '1', '3'], ['0', '1', '1']], [['1', '0', '2'], ['0', '1', '1']])],
        },
    },
    'infinitas': {
        'matriz': [['1', '1', '2'], ['2', '2', '4']],
        'texto': 'x1+x2=2;2x1+2x2=4',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1],
            'clasificacion': 'Consistente de soluciones infinitas',
            'ecuaciones_resultantes': ['x1 + x2 = 2', '0 = 0'],
            'solucion_general': ['x1 = 2 - x2', 'x2 es libre'],
            'expresiones_solucion': [{'constante': '2', 'coeficientes': {2: '-1'}}, {'constante': '0', 'coeficientes': {2: '1'}}],
            'soluciones': [],
            'fila_inconsistente': None,
            'filas_nulas': [{'fila': 2, 'termino_independiente': '0', 'representacion': ['0', '0', '0']}],
            'variables_libres': [2],
            'solucion_directa': False,
            'justificacion': ['En la fila 2 se obtiene [0 0 | 0], por lo que esa ecuación no agrega una nueva condición.', '',
             'La variable x2 no tiene pivote, por lo que es libre.'],
        },
        'final_html': ('Resultado final Clasificación Consistente de soluciones infinitas Solución En la fila 2 se obtiene [0 0 '
         '| 0], por lo que esa ecuación no agrega una nueva condición. La variable x2 no tiene pivote, por lo que '
         'es libre. x1 = 2 - x2 x2 es libre Columnas pivote Columnas pivote: C1 C1 Las columnas resaltadas en la '
         'matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '1', '2'], ['0', '0', '0']],
            'pasos_sustitucion': [],
            'sustitucion_web': [],
            'pasos': [('F2 = F2 - (2)F1', [['1', '1', '2'], ['2', '2', '4']], [['1', '1', '2'], ['0', '0', '0']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '1', '2'], ['0', '0', '0']],
            'sustitucion_web': [],
            'pasos_adicionales': [],
        },
    },
    'inconsistente': {
        'matriz': [['1', '1', '2'], ['2', '2', '5']],
        'texto': 'x1+x2=2;2x1+2x2=5',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1],
            'clasificacion': 'Inconsistente',
            'ecuaciones_resultantes': ['x1 + x2 = 2', '0 = 1'],
            'solucion_general': [],
            'soluciones': [],
            'fila_inconsistente': {'fila': 2, 'termino_independiente': '1', 'representacion': ['0', '0', '1']},
            'filas_nulas': [],
            'variables_libres': [],
            'solucion_directa': False,
            'justificacion': ['En la fila 2 se obtiene [0 0 | 1], que equivale a 0 = 1.', '',
             'Como esta igualdad es imposible, el sistema es inconsistente y no tiene solución.'],
        },
        'final_html': ('Resultado final Clasificación Inconsistente Solución En la fila 2 se obtiene [0 0 | 1], que equivale a '
         '0 = 1. Como esta igualdad es imposible, el sistema es inconsistente y no tiene solución. Columnas '
         'pivote Columnas pivote: C1 C1 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '1', '2'], ['0', '0', '1']],
            'pasos_sustitucion': [],
            'sustitucion_web': [],
            'pasos': [('F2 = F2 - (2)F1', [['1', '1', '2'], ['2', '2', '5']], [['1', '1', '2'], ['0', '0', '1']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '1', '2'], ['0', '0', '1']],
            'sustitucion_web': [],
            'pasos_adicionales': [],
        },
    },
    'rectangular': {
        'matriz': [['1', '0', '2'], ['0', '1', '3'], ['1', '1', '5']],
        'texto': 'x1=2;x2=3;x1+x2=5',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1, 2],
            'clasificacion': 'Consistente de solución única',
            'ecuaciones_resultantes': ['x1 = 2', 'x2 = 3', '0 = 0'],
            'solucion_general': ['x1 = 2', 'x2 = 3'],
            'expresiones_solucion': [{'constante': '2', 'coeficientes': {}}, {'constante': '3', 'coeficientes': {}}],
            'soluciones': ['2', '3'],
            'fila_inconsistente': None,
            'filas_nulas': [{'fila': 3, 'termino_independiente': '0', 'representacion': ['0', '0', '0']}],
            'variables_libres': [],
            'solucion_directa': True,
            'justificacion': [],
        },
        'final_html': ('Resultado final Clasificación Consistente de solución única Solución x1 = 2 x2 = 3 Columnas pivote '
         'Columnas pivote: C1, C2 C1 C2 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '0', '2'], ['0', '1', '3'], ['0', '0', '0']],
            'pasos_sustitucion': [{'variable': 2, 'expresion': '3', 'valor': '3'}, {'variable': 1, 'expresion': '2', 'valor': '2'}],
            'sustitucion_web': ['x2 = 3', 'x1 = 2'],
            'pasos': [('F3 = F3 - (1)F1', [['1', '0', '2'], ['0', '1', '3'], ['1', '1', '5']],
              [['1', '0', '2'], ['0', '1', '3'], ['0', '1', '3']]),
             ('F3 = F3 - (1)F2', [['1', '0', '2'], ['0', '1', '3'], ['0', '1', '3']],
              [['1', '0', '2'], ['0', '1', '3'], ['0', '0', '0']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '0', '2'], ['0', '1', '3'], ['0', '0', '0']],
            'sustitucion_web': [],
            'pasos_adicionales': [],
        },
    },
    'fracciones': {
        'matriz': [['1/2', '1/3', '1'], ['1/4', '-1/3', '0']],
        'texto': '1/2x1+1/3x2=1;1/4x1-1/3x2=0',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1, 2],
            'clasificacion': 'Consistente de solución única',
            'solucion_general': ['x1 = 4/3', 'x2 = 1'],
            'expresiones_solucion': [{'constante': '4/3', 'coeficientes': {}}, {'constante': '1', 'coeficientes': {}}],
            'soluciones': ['4/3', '1'],
            'fila_inconsistente': None,
            'filas_nulas': [],
            'variables_libres': [],
            'justificacion': [],
        },
        'final_html': ('Resultado final Clasificación Consistente de solución única Solución x1 = 4/3 x2 = 1 Columnas pivote '
         'Columnas pivote: C1, C2 C1 C2 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '2/3', '2'], ['0', '1', '1']],
            'pasos_sustitucion': [{'variable': 2, 'expresion': '1', 'valor': '1'},
             {'variable': 1, 'expresion': '2 - (2/3)(1)', 'valor': '4/3'}],
            'ecuaciones_resultantes': ['x1 + 2/3x2 = 2', 'x2 = 1'],
            'solucion_directa': False,
            'sustitucion_web': ['x2 = 1', 'x1 = 2 - (2/3)(1) = 4/3'],
            'pasos': [('F1 = (2)F1', [['1/2', '1/3', '1'], ['1/4', '-1/3', '0']],
              [['1', '2/3', '2'], ['1/4', '-1/3', '0']]),
             ('F2 = F2 - (1/4)F1', [['1', '2/3', '2'], ['1/4', '-1/3', '0']],
              [['1', '2/3', '2'], ['0', '-1/2', '-1/2']]),
             ('F2 = (-2)F2', [['1', '2/3', '2'], ['0', '-1/2', '-1/2']], [['1', '2/3', '2'], ['0', '1', '1']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '0', '4/3'], ['0', '1', '1']],
            'ecuaciones_resultantes': ['x1 = 4/3', 'x2 = 1'],
            'solucion_directa': True,
            'sustitucion_web': [],
            'pasos_adicionales': [('F1 = F1 - (2/3)F2', [['1', '2/3', '2'], ['0', '1', '1']], [['1', '0', '4/3'], ['0', '1', '1']])],
        },
    },
    'intercambio': {
        'matriz': [['0', '1', '3'], ['1', '2', '8']],
        'texto': 'x2=3;x1+2x2=8',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1, 2],
            'clasificacion': 'Consistente de solución única',
            'solucion_general': ['x1 = 2', 'x2 = 3'],
            'expresiones_solucion': [{'constante': '2', 'coeficientes': {}}, {'constante': '3', 'coeficientes': {}}],
            'soluciones': ['2', '3'],
            'fila_inconsistente': None,
            'filas_nulas': [],
            'variables_libres': [],
            'justificacion': [],
        },
        'final_html': ('Resultado final Clasificación Consistente de solución única Solución x1 = 2 x2 = 3 Columnas pivote '
         'Columnas pivote: C1, C2 C1 C2 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '2', '8'], ['0', '1', '3']],
            'pasos_sustitucion': [{'variable': 2, 'expresion': '3', 'valor': '3'},
             {'variable': 1, 'expresion': '8 - (2)(3)', 'valor': '2'}],
            'ecuaciones_resultantes': ['x1 + 2x2 = 8', 'x2 = 3'],
            'solucion_directa': False,
            'sustitucion_web': ['x2 = 3', 'x1 = 8 - (2)(3) = 2'],
            'pasos': [('F1 <-> F2', [['0', '1', '3'], ['1', '2', '8']], [['1', '2', '8'], ['0', '1', '3']])],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '0', '2'], ['0', '1', '3']],
            'ecuaciones_resultantes': ['x1 = 2', 'x2 = 3'],
            'solucion_directa': True,
            'sustitucion_web': [],
            'pasos_adicionales': [('F1 = F1 - (2)F2', [['1', '2', '8'], ['0', '1', '3']], [['1', '0', '2'], ['0', '1', '3']])],
        },
    },
    'columna_sin_pivote': {
        'matriz': [['1', '2', '3', '4'], ['0', '0', '1', '2']],
        'texto': 'x1+2x2+3x3=4;x3=2',
        'reescritas': [],
        'comun': {
            'columnas_pivote': [1, 3],
            'clasificacion': 'Consistente de soluciones infinitas',
            'solucion_general': ['x1 = -2 - 2x2', 'x2 es libre', 'x3 = 2'],
            'expresiones_solucion': [{'constante': '-2', 'coeficientes': {2: '-2'}}, {'constante': '0', 'coeficientes': {2: '1'}},
             {'constante': '2', 'coeficientes': {}}],
            'soluciones': [],
            'fila_inconsistente': None,
            'filas_nulas': [],
            'variables_libres': [2],
            'solucion_directa': False,
            'justificacion': ['La variable x2 no tiene pivote, por lo que es libre.'],
        },
        'final_html': ('Resultado final Clasificación Consistente de soluciones infinitas Solución La variable x2 no tiene '
         'pivote, por lo que es libre. x1 = -2 - 2x2 x2 es libre x3 = 2 Columnas pivote Columnas pivote: C1, C3 '
         'C1 C3 Las columnas resaltadas en la matriz final contienen un pivote.'),
        'gauss': {
            'matriz_escalonada': [['1', '2', '3', '4'], ['0', '0', '1', '2']],
            'pasos_sustitucion': [],
            'ecuaciones_resultantes': ['x1 + 2x2 + 3x3 = 4', 'x3 = 2'],
            'sustitucion_web': [],
            'pasos': [],
        },
        'gauss_jordan': {
            'matriz_reducida': [['1', '2', '0', '-2'], ['0', '0', '1', '2']],
            'ecuaciones_resultantes': ['x1 + 2x2 = -2', 'x3 = 2'],
            'sustitucion_web': [],
            'pasos_adicionales': [('F1 = F1 - (3)F2', [['1', '2', '3', '4'], ['0', '0', '1', '2']],
              [['1', '2', '0', '-2'], ['0', '0', '1', '2']])],
        },
    },
}
