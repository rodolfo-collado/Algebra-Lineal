"""Valida un tag estable contra pyproject y el HEAD remoto previamente actualizado."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import tomllib


def git_commit(ref):
    return subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], text=True
    ).strip()


def validate_release(ref):
    version = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    # La primera política de distribución solo admite versiones estables X.Y.Z.
    if not re.fullmatch(r"refs/tags/v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", ref):
        raise ValueError("Se requiere un tag estable refs/tags/vX.Y.Z.")
    if ref != f"refs/tags/v{version}":
        raise ValueError(f"El tag no coincide con project.version ({version}).")
    commit = git_commit(ref)
    if commit != git_commit("HEAD"):
        raise ValueError("El checkout no corresponde al commit etiquetado.")
    if commit != git_commit("refs/remotes/origin/main"):
        raise ValueError("El tag debe apuntar al HEAD actual de origin/main.")
    return version, commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    args = parser.parse_args()
    try:
        version, commit = validate_release(args.ref)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release rechazada: {error}\n")
    print(f"Tag validado: v{version} en {commit}")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"version={version}\ncommit={commit}\n")


if __name__ == "__main__":
    main()
