"""Comprueba la experiencia configurada en el instalador de Windows.

No se interpreta Inno Setup por completo: solo se leen las directivas y entradas
que definen el flujo (instalación por usuario, carpeta fija, resumen, tareas,
WebView2 y estilo del asistente) para que un cambio accidental se detecte antes
de compilar y probar el instalador a mano.
"""

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT_INNO = RAIZ / "installer" / "AlgebraLineal.iss"
SCRIPT_BUILD = RAIZ / "scripts" / "build_windows.ps1"
SCRIPT_PRUEBA = RAIZ / "scripts" / "test_windows_distribution.ps1"
WORKFLOW_CI = RAIZ / ".github" / "workflows" / "ci.yml"

APP_ID = "{D0455B79-7F5E-4C78-9F3B-F47187E9A83A}"
CARPETA_PREDETERMINADA = r"{localappdata}\Programs\AlgebraLineal"


def secciones():
    """Agrupa las líneas útiles del .iss por sección, sin comentarios ni vacíos."""
    resultado = {}
    actual = None
    for linea in SCRIPT_INNO.read_text(encoding="utf-8").splitlines():
        texto = linea.strip()
        if not texto or texto.startswith(";"):
            continue
        if re.fullmatch(r"\[[A-Za-z]+\]", texto):
            actual = texto[1:-1]
            resultado.setdefault(actual, [])
        elif actual is not None:
            resultado[actual].append(texto)
    return resultado


def directivas_setup():
    """Devuelve las directivas `Clave=Valor` de la sección [Setup]."""
    directivas = {}
    for linea in secciones()["Setup"]:
        clave, separador, valor = linea.partition("=")
        if separador:
            directivas[clave.strip()] = valor.strip()
    return directivas


def codigo_pascal():
    return "\n".join(secciones()["Code"])


class PruebasInstalacionPorUsuario(unittest.TestCase):
    def test_instala_por_usuario_sin_administrador(self):
        setup = directivas_setup()

        self.assertEqual(setup["PrivilegesRequired"], "lowest")
        self.assertEqual(setup["DefaultDirName"], CARPETA_PREDETERMINADA)
        self.assertEqual(setup["ArchitecturesInstallIn64BitMode"], "x64compatible")
        self.assertNotIn("PrivilegesRequiredOverridesAllowed", setup)

    def test_no_pregunta_la_carpeta_pero_la_informa_en_el_resumen(self):
        setup = directivas_setup()

        self.assertEqual(setup["DisableDirPage"], "yes")
        self.assertEqual(setup["AlwaysShowDirOnReadyPage"], "yes")
        self.assertNotIn("DisableReadyPage", setup)
        self.assertNotIn("DisableReadyMemo", setup)

        codigo = codigo_pascal()
        self.assertIn("function UpdateReadyMemo(", codigo)
        cuerpo = codigo.split("function UpdateReadyMemo(", 1)[1].split("\nend;", 1)[0]
        # La ruta debe aparecer una sola vez: la que entrega Setup en MemoDirInfo.
        self.assertEqual(cuerpo.count("MemoDirInfo"), 2, cuerpo)
        self.assertNotIn("WizardDirValue", cuerpo)
        self.assertNotIn("{app}", cuerpo)

    def test_la_carpeta_previa_se_conserva_al_actualizar(self):
        setup = directivas_setup()

        self.assertEqual(setup["AppId"], "{" + APP_ID)
        self.assertNotEqual(setup.get("UsePreviousAppDir", "yes"), "no")
        self.assertNotEqual(setup.get("Uninstallable", "yes"), "no")
        self.assertEqual(setup["UninstallDisplayName"], "{#AppName}")
        self.assertEqual(setup["UninstallDisplayIcon"], r"{app}\{#AppExe}")

    def test_la_prueba_manual_apunta_a_la_misma_instalacion(self):
        prueba = SCRIPT_PRUEBA.read_text(encoding="utf-8-sig")

        self.assertIn(f"Uninstall\\{APP_ID}_is1", prueba)
        self.assertIn("/DIR=", prueba)
        self.assertIn("cuenta limpia", prueba)
        self.assertIn("matrices/operaciones/", prueba)
        self.assertIn("matrices.js", prueba)
        # P13B viaja en el mismo smoke: AB y Ax comparando los dos procedimientos.
        self.assertIn("operacion = 'producto'", prueba)
        self.assertIn("operacion = 'matriz_vector'", prueba)
        self.assertIn('id="procedure-title-2"', prueba)


class PruebasFlujoDelAsistente(unittest.TestCase):
    def test_el_flujo_solo_pide_decisiones_utiles(self):
        setup = directivas_setup()
        partes = secciones()

        self.assertEqual(setup["DisableWelcomePage"], "yes")
        self.assertEqual(setup["DisableProgramGroupPage"], "yes")
        self.assertNotIn("Components", partes)
        self.assertNotIn("Types", partes)
        for directiva in ("LicenseFile", "InfoBeforeFile", "InfoAfterFile", "UserInfoPage"):
            self.assertNotIn(directiva, setup)

    def test_el_acceso_de_escritorio_es_opcional_y_el_de_inicio_es_normal(self):
        tareas = secciones()["Tasks"]
        iconos = secciones()["Icons"]

        self.assertEqual(len(tareas), 1)
        tarea = tareas[0]
        self.assertIn('Name: "desktopicon"', tarea)
        self.assertIn("acceso directo en el escritorio", tarea)
        self.assertIn("unchecked", tarea.split("Flags:", 1)[1])

        escritorio = [icono for icono in iconos if "{autodesktop}" in icono]
        inicio = [icono for icono in iconos if "{group}" in icono]
        self.assertEqual(len(escritorio), 1)
        self.assertIn("Tasks: desktopicon", escritorio[0])
        self.assertEqual(len(inicio), 1)
        self.assertNotIn("Tasks:", inicio[0])
        for icono in escritorio + inicio:
            self.assertIn(r"{app}\{#AppExe}", icono)

    def test_el_resumen_describe_accesos_directos_y_webview2(self):
        codigo = codigo_pascal()
        cuerpo = codigo.split("function UpdateReadyMemo(", 1)[1].split("\nend;", 1)[0]

        self.assertIn("'Accesos directos:'", cuerpo)
        self.assertIn("'Menú Inicio'", cuerpo)
        self.assertIn("WizardIsTaskSelected('desktopicon')", cuerpo)
        self.assertIn("'Escritorio'", cuerpo)
        self.assertIn("'Microsoft Edge WebView2 Runtime:'", cuerpo)
        self.assertIn("if NeedsWebView2 then", cuerpo)
        self.assertIn("Ya está disponible", cuerpo)
        self.assertIn("Se instalará como requisito", cuerpo)

    def test_ofrece_abrir_la_aplicacion_al_terminar(self):
        ejecuciones = secciones()["Run"]

        self.assertEqual(len(ejecuciones), 1)
        self.assertIn(r"{app}\{#AppExe}", ejecuciones[0])
        self.assertIn("postinstall", ejecuciones[0])
        self.assertIn("skipifsilent", ejecuciones[0])
        self.assertIn("Check: WebView2Installed", ejecuciones[0])

    def test_solo_espanol_sin_dialogo_de_idioma(self):
        idiomas = secciones()["Languages"]

        self.assertEqual(len(idiomas), 1)
        self.assertIn('MessagesFile: "compiler:Languages\\Spanish.isl"', idiomas[0])


class PruebasWebView2EnElInstalador(unittest.TestCase):
    def test_el_bootstrapper_solo_se_instala_si_falta_el_runtime(self):
        archivos = secciones()["Files"]
        bootstrapper = [
            archivo for archivo in archivos if "MicrosoftEdgeWebview2Setup.exe" in archivo
        ]

        self.assertEqual(len(bootstrapper), 1)
        self.assertIn("Check: NeedsWebView2", bootstrapper[0])
        self.assertIn("AfterInstall: InstallWebView2", bootstrapper[0])
        self.assertIn(r'DestDir: "{app}\prerequisites"', bootstrapper[0])

        codigo = codigo_pascal()
        self.assertIn("Result := not WebView2Installed;", codigo)
        self.assertIn("'/silent /install'", codigo)
        self.assertIn("RegQueryStringValue(Root, WebView2Key, 'pv', Version)", codigo)
        self.assertIn("PackVersionComponents(86, 0, 622, 0)", codigo)

    def test_la_descarga_del_bootstrapper_valida_la_firma_de_microsoft(self):
        build = SCRIPT_BUILD.read_text(encoding="utf-8-sig")

        self.assertIn("Get-AuthenticodeSignature", build)
        self.assertIn("O=Microsoft Corporation", build)
        self.assertNotIn("SkipCertificateCheck", build)


class PruebasIdentidadYEstilo(unittest.TestCase):
    def test_nombre_version_y_archivo_del_instalador(self):
        setup = directivas_setup()
        build = SCRIPT_BUILD.read_text(encoding="utf-8-sig")

        self.assertEqual(setup["AppName"], "{#AppName}")
        self.assertIn('#define AppName "Álgebra Lineal"', SCRIPT_INNO.read_text(encoding="utf-8"))
        self.assertEqual(setup["AppVersion"], "{#AppVersion}")
        self.assertEqual(setup["OutputBaseFilename"], "AlgebraLineal-Setup-{#AppVersion}")
        self.assertEqual(setup["OutputDir"], r"{#ProjectRoot}\dist\installer")
        self.assertIn('"/DAppVersion=$appVersion"', build)
        self.assertIn('dist\\installer\\AlgebraLineal-Setup-$appVersion.exe', build)

    def test_estilo_moderno_dinamico_sin_recursos_externos(self):
        setup = directivas_setup()

        self.assertEqual(setup["WizardStyle"], "modern dynamic windows11")
        for directiva in (
            "WizardStyleFile",
            "WizardStyleFileDynamicDark",
            "WizardImageFile",
            "WizardSmallImageFile",
            "WizardBackImageFile",
        ):
            self.assertNotIn(directiva, setup)

    def test_el_icono_del_instalador_es_el_de_la_aplicacion(self):
        setup = directivas_setup()

        self.assertEqual(setup["SetupIconFile"], r"{#ProjectRoot}\assets\algebra-lineal.ico")
        self.assertTrue((RAIZ / "assets" / "algebra-lineal.ico").is_file())

    def test_ci_compila_con_la_version_de_inno_setup_documentada(self):
        ci = WORKFLOW_CI.read_text(encoding="utf-8")
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")

        version = re.search(r"innosetup-(\d+\.\d+\.\d+)\.exe", ci)
        self.assertIsNotNone(version)
        self.assertIn(f"Inno Setup {version.group(1)}", readme)


if __name__ == "__main__":
    unittest.main()
