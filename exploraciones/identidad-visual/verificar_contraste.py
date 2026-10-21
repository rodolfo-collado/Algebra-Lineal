"""Comprueba pares de tokens sólidos; no sustituye la revisión visual o WCAG."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def luminancia(color):
    canales = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineales = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    return sum(c * peso for c, peso in zip(lineales, (0.2126, 0.7152, 0.0722)))


def contraste(a, b):
    claro, oscuro = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


assert abs(contraste('#000000', '#ffffff') - 21) < 0.001
resultados = []
for concepto, cuerpo in re.findall(r'body\[data-concept=(\w+)\]\{([^}]+)\}', (ROOT / 'conceptos.css').read_text(encoding='utf-8')):
    tokens = dict(re.findall(r'--([\w-]+):(#[\da-fA-F]{3,6})(?=;|\})', cuerpo + '}'))
    tokens = {k: '#' + ''.join(c * 2 for c in v[1:]) if len(v) == 4 else v for k, v in tokens.items()}
    for primer, segundo, minimo in [('ink','bg',4.5), ('muted','bg',4.5), ('muted','surface',4.5), ('muted','wash',4.5), ('muted','bar',4.5), ('on-accent','accent',4.5), ('input-border','surface',3), ('focus','bg',3)]:
        ratio = contraste(tokens[primer], tokens[segundo])
        resultados.append({'concepto':concepto, 'par':f'{primer}/{segundo}', 'contraste':round(ratio,2), 'minimo':minimo, 'resultado':'PASS' if ratio >= minimo else 'FAIL'})
assert len(resultados) == 24, 'Deben comprobarse los tres conceptos.'
print(json.dumps(resultados, ensure_ascii=False, indent=2))
assert all(r['resultado'] == 'PASS' for r in resultados), 'Hay pares de contraste insuficiente.'
