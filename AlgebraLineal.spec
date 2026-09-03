# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.building.build_main import Analysis, COLLECT, EXE, PYZ


PROJECT_ROOT = Path(SPECPATH).resolve()

datas = [
    (
        str(PROJECT_ROOT / "frontend" / "web" / "calculadora" / "templates"),
        "frontend/web/calculadora/templates",
    ),
    (
        str(PROJECT_ROOT / "frontend" / "web" / "calculadora" / "static"),
        "frontend/web/calculadora/static",
    ),
    (
        str(PROJECT_ROOT / "assets" / "algebra-lineal.ico"),
        "assets",
    ),
]

hiddenimports = [
    "frontend.web.algebra_web.settings",
    "frontend.web.algebra_web.urls",
    "frontend.web.algebra_web.wsgi",
    "frontend.web.calculadora.apps",
    "frontend.web.calculadora.forms",
    "frontend.web.calculadora.servicios",
    "frontend.web.calculadora.urls",
    "frontend.web.calculadora.views",
    "webview.platforms.edgechromium",
    "webview.platforms.winforms",
]

a = Analysis(
    [str(PROJECT_ROOT / "desktop.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    [],
    name="AlgebraLineal",
    exclude_binaries=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    icon=str(PROJECT_ROOT / "assets" / "algebra-lineal.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="AlgebraLineal",
)
