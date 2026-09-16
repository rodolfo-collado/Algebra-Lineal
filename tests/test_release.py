"""Política de publicación y contratos críticos entre CI, build y CD."""

from contextlib import chdir
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from scripts.validate_release import validate_release


RAIZ = Path(__file__).resolve().parents[1]


class PruebasTagRelease(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "--quiet")
        tree = self.git("mktree", entrada="")
        # Objetos de prueba aislados; no se modifica la configuración/identidad Git.
        self.commit = self.git(
            "hash-object", "-t", "commit", "-w", "--stdin",
            entrada=f"tree {tree}\nauthor Test <test@example.invalid> 0 +0000\n"
                    "committer Test <test@example.invalid> 0 +0000\n\nFixture\n",
        )
        self.git("update-ref", "refs/heads/main", self.commit)
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        self.git("update-ref", "refs/remotes/origin/main", self.commit)
        self.git("update-ref", "refs/tags/v1.2.3", self.commit)
        (self.repo / "pyproject.toml").write_text(
            '[project]\nversion = "1.2.3"\n', encoding="utf-8"
        )

    def git(self, *args, entrada=None):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args],
            input=entrada.encode("utf-8") if entrada is not None else None,
            stderr=subprocess.PIPE,
        ).decode("utf-8").strip()

    def validar(self, ref="refs/tags/v1.2.3"):
        with chdir(self.repo):
            return validate_release(ref)

    def test_acepta_tag_ligero_en_head_de_main(self):
        self.assertEqual(self.validar(), ("1.2.3", self.commit))

    def test_acepta_tag_anotado_resolviendo_su_commit(self):
        tag = self.git(
            "mktag", entrada=f"object {self.commit}\ntype commit\ntag v1.2.3\n"
                             "tagger Test <test@example.invalid> 0 +0000\n\nRelease\n",
        )
        self.git("update-ref", "refs/tags/v1.2.3", tag)
        self.assertEqual(self.validar(), ("1.2.3", self.commit))

    def test_rechaza_ramas_y_formatos_no_estables(self):
        for ref in ("", "refs/heads/main", "refs/heads/develop", "v1.2.3",
                    "refs/tags/v1.2.3-rc1", "refs/tags/v1.2.3.4", "refs/tags/v01.2.3"):
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError, "tag estable"):
                self.validar(ref)

    def test_rechaza_version_distinta_sin_reescribir_pyproject(self):
        before = (self.repo / "pyproject.toml").read_bytes()
        with self.assertRaisesRegex(ValueError, "project.version"):
            self.validar("refs/tags/v9.8.7")
        self.assertEqual((self.repo / "pyproject.toml").read_bytes(), before)

    def otro_commit(self):
        tree = self.git("mktree", entrada="")
        return self.git(
            "hash-object", "-t", "commit", "-w", "--stdin",
            entrada=f"tree {tree}\nparent {self.commit}\n"
                    "author Test <test@example.invalid> 1 +0000\n"
                    "committer Test <test@example.invalid> 1 +0000\n\nNext\n",
        )

    def test_rechaza_tag_ancestro_de_main_aunque_este_integrado(self):
        self.git("update-ref", "refs/remotes/origin/main", self.otro_commit())
        with self.assertRaisesRegex(ValueError, "HEAD actual de origin/main"):
            self.validar()

    def test_rechaza_tag_feature_no_integrado(self):
        feature = self.otro_commit()
        self.git("update-ref", "refs/heads/main", feature)
        self.git("update-ref", "refs/tags/v1.2.3", feature)
        with self.assertRaisesRegex(ValueError, "HEAD actual de origin/main"):
            self.validar()

    def test_rechaza_checkout_ajeno_al_tag(self):
        self.git("update-ref", "refs/heads/main", self.otro_commit())
        with self.assertRaisesRegex(ValueError, "checkout"):
            self.validar()


class PruebasWorkflowRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = (RAIZ / ".github/workflows/release.yml").read_text(encoding="utf-8")
        cls.ci = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        cls.publicar = cls.release.split("\n  publicar:\n", 1)[1]

    def test_solo_tags_disparan_release(self):
        trigger = self.release.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertRegex(trigger, r"push:\s+tags:\s+- 'v\*\.\*\.\*'")
        for forbidden in ("branches:", "workflow_dispatch", "pull_request", "workflow_run"):
            self.assertNotIn(forbidden, trigger)

    def test_validacion_precede_ci_y_publicacion(self):
        self.assertIn("python3 scripts/validate_release.py", self.release)
        self.assertIn("git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main", self.release)
        self.assertIn("needs: validar", self.release)
        self.assertIn("uses: ./.github/workflows/ci.yml", self.release)
        self.assertIn("workflow_call:", self.ci)
        self.assertIn("needs: [validar, comprobar]", self.publicar)
        self.assertNotIn("always()", self.publicar)
        self.assertNotIn("continue-on-error", self.release + self.ci)
        self.assertIn("steps.tag.outputs.version", self.release)

    def test_solo_publicacion_tiene_escritura(self):
        self.assertEqual((self.release + self.ci).count("contents: write"), 1)
        self.assertIn("contents: write", self.publicar)
        self.assertIn("contents: read", self.release.split("jobs:")[0])
        self.assertNotIn("actions/checkout@", self.publicar)
        self.assertNotIn("pull_request_target", self.release + self.ci)

    def test_ci_ejecuta_checks_build_y_smoke_existentes(self):
        for command in ("uv lock --check", "uv sync --locked",
                        "uv run --locked python -m unittest discover -v",
                        "uv run --locked python manage.py check",
                        "uv run --locked python -m compileall -q backend frontend tests main.py manage.py desktop.py"):
            self.assertIn(command, self.ci)
        windows = self.ci.split("\n  windows:\n", 1)[1]
        self.assertIn("python -m unittest discover -v", windows)
        self.assertLess(windows.index("scripts\\build_windows.ps1"), windows.index("scripts\\test_windows_distribution.ps1"))
        self.assertIn("-InstallerPath $installers[0].FullName", windows)
        self.assertIn("if ($installers.Count -ne 1)", windows)
        self.assertIn("dist/installer/AlgebraLineal-Setup-*.exe", windows)

    def test_actions_fijadas_a_sha(self):
        for workflow in (self.ci, self.release):
            for action in re.findall(r"uses: ([^\s]+)", workflow):
                if not action.startswith("./"):
                    self.assertRegex(action, r"^[\w-]+/[\w-]+@[a-f0-9]{40}$")

    def test_revalida_refs_y_no_sobrescribe_releases(self):
        for marker in ('git/ref/heads/main', 'commits/$TAG',
                       '"$COMMIT" != "$current_main"', '"$COMMIT" != "$current_tag"',
                       '--paginate', 'grep -Fxq -- "$TAG"', 'set -euo pipefail'):
            self.assertIn(marker, self.publicar)
        self.assertNotIn("--clobber", self.publicar)
        self.assertIn("cancel-in-progress: false", self.release)

    def test_publica_solo_instalador_y_checksum_con_notas(self):
        for marker in ('installer="AlgebraLineal-Setup-$VERSION.exe"',
                       'sha256sum "$installer" > SHA256SUMS.txt',
                       'sha256sum --check SHA256SUMS.txt',
                       'gh release create "$TAG" "$installer" SHA256SUMS.txt',
                       '--verify-tag --draft', '--generate-notes',
                       'gh release edit "$TAG" --draft=false --latest'):
            self.assertIn(marker, self.publicar)
        for forbidden in ("MicrosoftEdgeWebview2Setup", "pyinstaller", "0.2.0"):
            self.assertNotIn(forbidden, self.publicar)


if __name__ == "__main__":
    unittest.main()
