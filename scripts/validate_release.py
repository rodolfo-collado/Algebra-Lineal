"""Valida sin escribir refs el candidato del push a main y deriva su tag estable."""

import argparse
import os
import re
import subprocess
import tomllib


STABLE_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def version_numbers(version):
    if not isinstance(version, str) or not STABLE_VERSION.fullmatch(version):
        raise ValueError("project.version debe ser una versión estable X.Y.Z sin ceros iniciales.")
    return tuple(map(int, version.split(".")))


def git_commit(ref):
    return subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], text=True
    ).strip()


def validate_release(ref, sha):
    if ref != "refs/heads/main":
        raise ValueError("El candidato debe venir de refs/heads/main.")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Se requiere el SHA completo del evento de push.")
    commit = git_commit("HEAD")
    if commit != sha:
        raise ValueError("El checkout no corresponde al SHA del evento de push.")
    project = subprocess.check_output(
        ["git", "show", f"{commit}:pyproject.toml"], encoding="utf-8"
    )
    version = tomllib.loads(project)["project"]["version"]
    candidate = version_numbers(version)
    tag = f"v{version}"
    tags = subprocess.check_output(
        ["git", "for-each-ref", "--format=%(refname:strip=2)", "refs/tags/"], text=True
    ).splitlines()
    if tag in tags and git_commit(f"refs/tags/{tag}") != commit:
        raise ValueError(f"{tag} ya pertenece a otro commit; nunca se mueve un tag estable.")
    stable = [version_numbers(name[1:]) for name in tags
              if name.startswith("v") and STABLE_VERSION.fullmatch(name[1:])]
    # La igualdad solo puede ser el tag canónico del mismo commit, para reintentos.
    if stable and candidate < max(stable):
        latest = ".".join(map(str, max(stable)))
        raise ValueError(f"La versión {version} es regresiva frente a v{latest}.")
    return version, tag, commit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args()
    try:
        version, tag, commit = validate_release(args.ref, args.sha)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release rechazada: {error}\n")
    print(f"Candidato validado: {tag} en {commit}")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"version={version}\ntag={tag}\ncommit={commit}\n")


if __name__ == "__main__":
    main()
