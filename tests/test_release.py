"""Candidatos de main y contratos críticos entre CI, build y publicación."""

from contextlib import chdir
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.validate_release import main, validate_release


RAIZ = Path(__file__).resolve().parents[1]


def bloque(texto, clave):
    """Extrae un bloque YAML por su nivel real de sangría, sin fijar espacios."""
    lineas = texto.splitlines()
    patron = re.compile(r"^(\s*)" + re.escape(clave) + r":(?:\s|$)")
    for indice, linea in enumerate(lineas):
        match = patron.match(linea)
        if not match:
            continue
        nivel = len(match[1])
        fin = indice + 1
        while fin < len(lineas):
            siguiente = lineas[fin]
            if siguiente.strip() and not siguiente.lstrip().startswith("#"):
                if len(siguiente) - len(siguiente.lstrip()) <= nivel:
                    break
            fin += 1
        return "\n".join(lineas[indice:fin])
    raise AssertionError(f"No existe el bloque YAML {clave}")


def lista(texto, clave):
    return re.findall(r"^\s*-\s+([^\s#]+)", bloque(texto, clave), flags=re.M)


class PruebasCandidatoRelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "--quiet")
        # Objetos aislados: no se cambia la identidad/configuración Git.
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        self.version("1.2.3")
        self.git("update-ref", "refs/remotes/origin/main", self.commit)

    def git(self, *args, entrada=None):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args],
            input=entrada.encode("utf-8") if entrada is not None else None,
            stderr=subprocess.PIPE,
        ).decode("utf-8").strip()

    def nuevo_commit(self, parent=None):
        padre = f"parent {parent}\n" if parent else ""
        return self.git(
            "hash-object", "-t", "commit", "-w", "--stdin",
            entrada=f"tree {self.tree}\n{padre}author Test <test@example.invalid> 0 +0000\n"
                    "committer Test <test@example.invalid> 0 +0000\n\nFixture\n",
        )

    def version(self, version):
        (self.repo / "pyproject.toml").write_text(
            f'[project]\nversion = "{version}"\n', encoding="utf-8"
        )
        blob = self.git("hash-object", "-w", "pyproject.toml")
        self.tree = self.git("mktree", entrada=f"100644 blob {blob}\tpyproject.toml\n")
        self.commit = self.nuevo_commit()
        self.git("update-ref", "refs/heads/main", self.commit)

    def validar(self, ref="refs/heads/main", sha=None):
        with chdir(self.repo):
            return validate_release(ref, self.commit if sha is None else sha)

    def test_acepta_main_y_deriva_tag_y_sha(self):
        self.assertEqual(self.validar(), ("1.2.3", "v1.2.3", self.commit))

    def test_rechaza_develop_y_otras_refs(self):
        for ref in ("", "refs/heads/develop", "refs/heads/feature/demo",
                    "main", "refs/tags/v1.2.3", "refs/pull/1/merge"):
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError, "refs/heads/main"):
                self.validar(ref)

    def test_versiones_estables(self):
        for version in ("0.0.0", "0.8.0", "0.10.0", "1.2.3", "10.20.300"):
            self.version(version)
            with self.subTest(version=version):
                self.assertEqual(self.validar(), (version, f"v{version}", self.commit))

    def test_rechaza_versiones_no_estables(self):
        for version in ("1.2.3-rc1", "1.2.3+build", "1.2.3.4", "01.2.3",
                        "1.02.3", "1.2.03", "v1.2.3", "1.2", "", " 1.2.3",
                        "1.2.٣", "1.2.3\n"):
            # TOML necesita escapar el salto literal de este caso.
            self.version(version.replace("\n", "\\n"))
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "versión estable"):
                self.validar()

    def test_rechaza_sha_incompleto_o_ajeno(self):
        for sha in ("", self.commit[:7], "main", "0" * 40):
            with self.subTest(sha=sha), self.assertRaisesRegex(ValueError, "SHA"):
                self.validar(sha=sha)

    def test_rechaza_checkout_distinto_del_evento(self):
        self.git("update-ref", "refs/heads/main", self.nuevo_commit(self.commit))
        with self.assertRaisesRegex(ValueError, "checkout"):
            self.validar()

    def test_main_puede_avanzar_durante_el_build(self):
        self.git("update-ref", "refs/remotes/origin/main", self.nuevo_commit(self.commit))
        self.assertEqual(self.validar(), ("1.2.3", "v1.2.3", self.commit))

    def test_no_modifica_archivos_ni_refs_al_aceptar_o_rechazar(self):
        before = (self.repo / "pyproject.toml").read_bytes()
        refs = self.git("show-ref")
        self.validar()
        with self.assertRaises(ValueError):
            self.validar("refs/heads/develop")
        self.assertEqual((self.repo / "pyproject.toml").read_bytes(), before)
        self.assertEqual(self.git("show-ref"), refs)

    def test_lee_la_version_del_commit_no_de_archivos_locales(self):
        (self.repo / "pyproject.toml").write_text('[project]\nversion = "9.9.9"\n', encoding="utf-8")
        self.assertEqual(self.validar(), ("1.2.3", "v1.2.3", self.commit))

    def test_rechaza_tag_de_otro_commit(self):
        self.git("update-ref", "refs/tags/v1.2.3", self.nuevo_commit(self.commit))
        with self.assertRaisesRegex(ValueError, "otro commit"):
            self.validar()

    def test_reutiliza_tag_ligero_del_mismo_commit(self):
        self.git("update-ref", "refs/tags/v1.2.3", self.commit)
        self.assertEqual(self.validar(), ("1.2.3", "v1.2.3", self.commit))

    def test_reutiliza_tag_anotado_del_mismo_commit(self):
        tag = self.git(
            "mktag", entrada=f"object {self.commit}\ntype commit\ntag v1.2.3\n"
                             "tagger Test <test@example.invalid> 0 +0000\n\nRelease\n",
        )
        self.git("update-ref", "refs/tags/v1.2.3", tag)
        self.assertEqual(self.validar(), ("1.2.3", "v1.2.3", self.commit))

    def test_version_repetida_de_nuevo_commit_se_rechaza(self):
        self.git("update-ref", "refs/tags/v1.2.3", self.commit)
        nuevo = self.nuevo_commit(self.commit)
        self.git("update-ref", "refs/heads/main", nuevo)
        with self.assertRaisesRegex(ValueError, "otro commit"):
            self.validar(sha=nuevo)

    def test_comparacion_numerica_acepta_010_despues_de_09(self):
        self.version("0.10.0")
        self.git("update-ref", "refs/tags/v0.9.0", self.commit)
        self.assertEqual(self.validar()[0], "0.10.0")

    def test_rechaza_version_regresiva(self):
        self.version("0.9.0")
        self.git("update-ref", "refs/tags/v0.10.0", self.commit)
        with self.assertRaisesRegex(ValueError, "regresiva"):
            self.validar()

    def test_reintento_no_puede_publicar_por_debajo_de_una_version_posterior(self):
        self.git("update-ref", "refs/tags/v1.2.3", self.commit)
        self.git("update-ref", "refs/tags/v1.3.0", self.nuevo_commit(self.commit))
        with self.assertRaisesRegex(ValueError, "regresiva"):
            self.validar()

    def test_ignora_tags_no_estables(self):
        for tag in ("v9.0.0-rc1", "v99.0.0.1", "v01.0.0", "backup", "9.0.0"):
            self.git("update-ref", f"refs/tags/{tag}", self.commit)
        self.assertEqual(self.validar()[0], "1.2.3")

    def test_cli_emite_version_tag_y_commit(self):
        output = self.repo / "outputs"
        with chdir(self.repo), patch.dict(os.environ, {
            "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": self.commit,
            "GITHUB_OUTPUT": str(output),
        }), patch("sys.argv", ["validate_release.py"]):
            main()
        self.assertEqual(output.read_text(encoding="utf-8"),
                         f"version=1.2.3\ntag=v1.2.3\ncommit={self.commit}\n")


class PruebasWorkflowRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = (RAIZ / ".github/workflows/release.yml").read_text(encoding="utf-8")
        cls.ci = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        cls.validar = bloque(bloque(cls.release, "jobs"), "validar")
        cls.comprobar = bloque(bloque(cls.release, "jobs"), "comprobar")
        cls.publicar = bloque(bloque(cls.release, "jobs"), "publicar")

    def test_solo_push_main_dispara_release(self):
        trigger = bloque(self.release, "on")
        self.assertEqual(lista(bloque(trigger, "push"), "branches"), ["main"])
        for forbidden in ("tags:", "workflow_dispatch", "pull_request", "workflow_run"):
            self.assertNotIn(forbidden, trigger)

    def test_validacion_precede_ci_y_creacion_del_tag(self):
        self.assertIn("python3 scripts/validate_release.py", self.validar)
        self.assertRegex(self.comprobar, r"needs:\s*validar")
        self.assertIn("uses: ./.github/workflows/ci.yml", self.comprobar)
        self.assertRegex(self.publicar, r"needs:\s*\[\s*validar\s*,\s*comprobar\s*\]")
        for forbidden in ("always()", "continue-on-error"):
            self.assertNotIn(forbidden, self.release + self.ci)
        self.assertNotIn("--method POST", self.validar + self.comprobar)
        self.assertLess(self.publicar.index('git/tags"'), self.publicar.index('git/refs"'))
        self.assertLess(self.publicar.index('git/refs"'), self.publicar.index('gh release create'))
        for name in ("version", "tag", "commit"):
            self.assertIn(f"steps.candidato.outputs.{name}", self.validar)

    def test_checkout_y_assets_anclados_al_sha_del_evento(self):
        self.assertIn("ref: ${{ github.sha }}", self.validar)
        self.assertIn("fetch-depth: 0", self.validar)
        self.assertEqual(self.ci.count("ref: ${{ github.sha }}"), 2)
        self.assertIn("needs.validar.outputs.commit", self.publicar)
        self.assertIn("needs.validar.outputs.tag", self.publicar)
        self.assertIn('-f object="$COMMIT"', self.publicar)
        self.assertIn('--target "$COMMIT"', self.publicar)
        self.assertNotIn("git/ref/heads/main", self.publicar)
        self.assertNotIn("github.ref_name", self.publicar)

    def test_solo_publicacion_tiene_escritura(self):
        self.assertEqual(len(re.findall(r"contents:\s*write", self.release + self.ci)), 1)
        self.assertRegex(bloque(self.publicar, "permissions"), r"contents:\s*write")
        self.assertRegex(bloque(self.release, "permissions"), r"contents:\s*read")
        self.assertRegex(bloque(self.ci, "permissions"), r"contents:\s*read")
        self.assertNotIn("actions/checkout@", self.publicar)
        self.assertEqual((self.validar + self.ci).count("persist-credentials: false"), 3)
        self.assertNotIn("pull_request_target", self.release + self.ci)

    def test_ci_cubre_develop_y_pr_main_sin_duplicar_push_main(self):
        trigger = bloque(self.ci, "on")
        self.assertIn("workflow_call:", trigger)
        self.assertEqual(lista(bloque(trigger, "push"), "branches"), ["develop"])
        self.assertEqual(set(lista(bloque(trigger, "pull_request"), "branches")), {"develop", "main"})

    def test_ci_ejecuta_checks_build_y_smoke_existentes(self):
        for command in ("uv lock --check", "uv sync --locked",
                        "uv run --locked python -m unittest discover -v",
                        "uv run --locked python manage.py check",
                        "uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py"):
            self.assertIn(command, self.ci)
        windows = bloque(bloque(self.ci, "jobs"), "windows")
        self.assertIn("python -m unittest discover -v", windows)
        self.assertLess(windows.index("scripts\\build_windows.ps1"), windows.index("scripts\\test_windows_distribution.ps1"))
        self.assertIn("-InstallerPath $installers[0].FullName", windows)
        self.assertIn("if ($installers.Count -ne 1)", windows)
        self.assertIn("dist/installer/AlgebraLineal-Setup-*.exe", windows)

    def test_actions_fijadas_a_sha(self):
        for workflow in (self.ci, self.release):
            for action in re.findall(r"uses:\s*([^\s]+)", workflow):
                if not action.startswith("./"):
                    self.assertRegex(action, r"^[\w-]+/[\w-]+@[a-f0-9]{40}$")

    def test_revisa_tags_remotos_y_reutiliza_solo_el_mismo_commit(self):
        for marker in ('git/matching-refs/tags/', 'commits/refs/tags/$TAG',
                       '"$COMMIT" != "$current_tag"', "sort -V",
                       'refs/tags/$TAG', "tag_exists=true", "tag_exists=false",
                       "if: steps.remoto.outputs.tag_exists == 'false'"):
            self.assertIn(marker, self.publicar)
        for forbidden in ("--force", "method PATCH", "method DELETE"):
            self.assertNotIn(forbidden, self.publicar)
        self.assertIn('-f message="PyGebra $TAG"', self.publicar)
        self.assertIn("-f type=commit", self.publicar)

    def test_no_sobrescribe_release_ni_draft(self):
        self.assertIn('--paginate', self.publicar)
        self.assertIn('grep -Fxq -- "$TAG"', self.publicar)
        self.assertNotIn("--clobber", self.publicar)
        self.assertNotIn("--exclude-drafts", self.publicar)
        self.assertLess(self.publicar.index('repos/$GH_REPO/releases'), self.publicar.index('git/tags"'))

    def test_concurrencia_no_cancela_publicaciones_ni_sustituye_pendientes(self):
        concurrency = bloque(self.release, "concurrency")
        self.assertRegex(concurrency, r"cancel-in-progress:\s*false")
        self.assertRegex(concurrency, r"queue:\s*max")
        ci_concurrency = bloque(self.ci, "concurrency")
        self.assertIn("github.ref != 'refs/heads/main'", ci_concurrency)
        self.assertIn("github.run_id", ci_concurrency)

    def test_publica_solo_instalador_y_checksum_con_notas(self):
        for marker in ('name: algebra-lineal-windows',
                       'installer="AlgebraLineal-Setup-$VERSION.exe"',
                       'sha256sum "$installer" > SHA256SUMS.txt',
                       'sha256sum --check SHA256SUMS.txt',
                       'gh release create "$TAG" "$installer" SHA256SUMS.txt',
                       '--verify-tag --draft', '--generate-notes', '--title "PyGebra $TAG"',
                       'gh release edit "$TAG" --draft=false --latest'):
            self.assertIn(marker, self.publicar)
        self.assertLess(self.publicar.index('git/refs"'), self.publicar.index('sha256sum "$installer"'))
        self.assertLess(self.publicar.index("actions/download-artifact@"), self.publicar.index('sha256sum "$installer"'))
        self.assertLess(self.publicar.index('sha256sum --check SHA256SUMS.txt'), self.publicar.index('gh release create'))
        for forbidden in ("MicrosoftEdgeWebview2Setup", "pyinstaller", "build/"):
            self.assertNotIn(forbidden, self.publicar)

    def test_verifica_ambos_assets_del_draft_antes_de_publicar(self):
        for marker in ('gh release view "$TAG" --json assets', 'gh release download "$TAG"',
                       'cmp SHA256SUMS.txt verified/SHA256SUMS.txt',
                       '(cd verified && sha256sum --check SHA256SUMS.txt)'):
            self.assertIn(marker, self.publicar)
        self.assertLess(self.publicar.index("gh release create"), self.publicar.index("gh release download"))
        self.assertLess(self.publicar.index("gh release download"), self.publicar.index("gh release edit"))


class PruebasPublicacionAislada(unittest.TestCase):
    """Ejecuta Bash con una API ficticia; nunca usa GitHub ni crea refs reales."""

    @classmethod
    def setUpClass(cls):
        if os.name == "nt":
            git = shutil.which("git")
            cls.bash = Path(git).resolve().parents[1] / "bin/bash.exe" if git else None
            if not cls.bash or not cls.bash.is_file():
                raise unittest.SkipTest("Git Bash no está disponible")
        else:
            cls.bash = shutil.which("bash")
            if not cls.bash:
                raise unittest.SkipTest("Bash no está disponible")
        workflow = (RAIZ / ".github/workflows/release.yml").read_text(encoding="utf-8")
        publicar = bloque(bloque(workflow, "jobs"), "publicar")
        cls.scripts = []
        lineas = publicar.splitlines()
        for indice, linea in enumerate(lineas):
            if linea.strip() != "run: |":
                continue
            nivel = len(linea) - len(linea.lstrip())
            contenido = []
            for siguiente in lineas[indice + 1:]:
                if siguiente.strip() and len(siguiente) - len(siguiente.lstrip()) <= nivel:
                    break
                contenido.append(siguiente[nivel + 2:])
            cls.scripts.append("\n".join(contenido))
        cls.guard = next(script for script in cls.scripts if "stable_versions=" in script)
        cls.tag = next(script for script in cls.scripts if "tag_object=" in script)
        cls.publish = next(script for script in cls.scripts if "gh release create" in script)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.sha = "a" * 40
        self.env = {**os.environ, "GH_TOKEN": "fixture", "GH_REPO": "test/fixture",
                    "VERSION": "0.10.0", "TAG": "v0.10.0", "COMMIT": self.sha,
                    "TAG_SHA": self.sha, "REFS": "refs/tags/v0.9.0",
                    "RELEASES": "", "GITHUB_OUTPUT": "outputs", "FAIL_API": "",
                    "CORRUPT": "", "FAIL_REF": ""}

    def ejecutar(self, script, **env):
        api = r'''
gh() {
  printf '%s\n' "$*" >> calls
  if [[ -n "$FAIL_API" ]]; then return 42; fi
  case "$1 $2" in
    "api repos/test/fixture/releases") printf '%s\n' "$RELEASES" ;;
    "api repos/test/fixture/git/matching-refs/tags/") printf '%s\n' "$REFS" ;;
    "api repos/test/fixture/commits/refs/tags/v0.10.0") printf '%s\n' "$TAG_SHA" ;;
    "api --method")
      if [[ "$4" == */git/tags ]]; then printf '%040d\n' 1
      elif [[ "$4" == */git/refs && -z "$FAIL_REF" ]]; then return 0
      else return 1; fi ;;
    "release create"|"release edit") return 0 ;;
    "release view") printf 'AlgebraLineal-Setup-0.10.0.exe\nSHA256SUMS.txt\n' ;;
    "release download")
      mkdir verified
      cp AlgebraLineal-Setup-0.10.0.exe SHA256SUMS.txt verified/
      if [[ -n "$CORRUPT" ]]; then printf 'corrupto' > verified/AlgebraLineal-Setup-0.10.0.exe; fi ;;
    *) return 99 ;;
  esac
}
'''
        return subprocess.run([str(self.bash)], input=api + "\n" + script, text=True,
                              encoding="utf-8", capture_output=True, cwd=self.repo,
                              env={**self.env, **env})

    def test_guard_acepta_version_numerica_nueva(self):
        result = self.ejecutar(self.guard)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "outputs").read_text().strip(), "tag_exists=false")

    def test_guard_reutiliza_tag_del_mismo_sha(self):
        result = self.ejecutar(self.guard, REFS="refs/tags/v0.10.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "outputs").read_text().strip(), "tag_exists=true")

    def test_guard_rechaza_otro_sha_version_regresiva_release_y_error_api(self):
        for env in ({"REFS": "refs/tags/v0.10.0", "TAG_SHA": "b" * 40},
                    {"REFS": "refs/tags/v0.11.0"}, {"RELEASES": "v0.10.0"},
                    {"FAIL_API": "true"}):
            with self.subTest(env=env):
                self.assertNotEqual(self.ejecutar(self.guard, **env).returncode, 0)
                self.assertFalse((self.repo / "outputs").exists())

    def test_tag_anotado_usa_sha_candidato_y_falla_sin_mover_refs(self):
        result = self.ejecutar(self.tag)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.repo / "calls").read_text()
        self.assertIn(f"object={self.sha}", calls)
        self.assertIn("type=commit", calls)
        self.assertIn("message=PyGebra v0.10.0", calls)
        self.assertNotEqual(self.ejecutar(self.tag, FAIL_REF="true").returncode, 0)

    def test_draft_se_publica_solo_tras_verificar_descargas(self):
        (self.repo / "AlgebraLineal-Setup-0.10.0.exe").write_bytes(b"installer ficticio")
        result = self.ejecutar(self.publish)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.repo / "calls").read_text()
        self.assertLess(calls.index("release create"), calls.index("release download"))
        self.assertLess(calls.index("release download"), calls.index("release edit"))

    def test_asset_corrupto_detiene_publicacion_del_draft(self):
        (self.repo / "AlgebraLineal-Setup-0.10.0.exe").write_bytes(b"installer ficticio")
        result = self.ejecutar(self.publish, CORRUPT="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("release edit", (self.repo / "calls").read_text())


if __name__ == "__main__":
    unittest.main()
