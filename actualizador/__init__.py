"""Actualizador de la app de escritorio a partir de las releases estables de GitHub.

Cada módulo tiene una responsabilidad y se prueba por separado:

- ``versiones``: versión instalada y comparación de versiones estables.
- ``releases``: consulta de la release estable más reciente y de sus artefactos.
- ``descarga``: descarga a un archivo temporal con tamaño verificado.
- ``verificacion``: SHA-256 frente al ``SHA256SUMS.txt`` publicado.
- ``instalador``: verifica de nuevo y entrega el control a Inno Setup.
- ``servicio``: estado del flujo para la interfaz; solo actúa cuando el usuario lo pide.
"""
