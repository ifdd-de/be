"""Check the image setup of a rendered instance.

    python tests/check_image.py <rendered instance>

The backend uses a plain python base image and starts uvicorn directly (no
gunicorn, no tiangolo base image). start.sh runs prestart.sh and then uvicorn
with the app factory; the dev image uses start-reload.sh with --reload. Both
images run as an unprivileged user, not as root.
"""

import sys
from pathlib import Path


def code_lines(text):
    """Non-comment, non-blank lines, for checks that must ignore comments."""
    return [l for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]


ROOT_USERS = {"root", "0"}


def user_problems(dockerfile, lines):
    """The container must not run as root: the last USER is not root."""
    users = [l.split(None, 1)[1].strip() for l in lines if l.startswith("USER ")]
    if not users:
        return [f"{dockerfile}: no USER, the container runs as root"]
    user = users[-1]
    if user.split(":")[0] in ROOT_USERS:
        return [f"{dockerfile}: runs as root (USER {user})"]
    return []


def main(instance):
    inst = Path(instance)
    errors = []

    for dockerfile in ("Dockerfile", "Dockerfile.dev"):
        lines = code_lines((inst / dockerfile).read_text())
        first = next(l for l in lines if l.startswith("FROM "))
        if not first.startswith("FROM python:"):
            errors.append(f"{dockerfile}: base image is not python:*, got {first!r}")
        if any("tiangolo" in l for l in lines):
            errors.append(f"{dockerfile}: still uses the tiangolo base image")
        if any("gunicorn" in l for l in lines):
            errors.append(f"{dockerfile}: runs gunicorn")
        errors += user_problems(dockerfile, lines)

    for script, needs_reload in (("start.sh", False), ("start-reload.sh", True)):
        path = inst / script
        if not path.exists():
            errors.append(f"{script} missing")
            continue
        lines = code_lines(path.read_text())
        body = "\n".join(lines)
        if "uvicorn" not in body or "ifdd.be.core:create_app" not in body:
            errors.append(f"{script}: does not start the ifdd-be-core app with uvicorn")
        if any("gunicorn" in l for l in lines):
            errors.append(f"{script}: runs gunicorn")
        if "prestart.sh" not in body:
            errors.append(f"{script}: does not run prestart.sh")
        if needs_reload and "--reload" not in body:
            errors.append(f"{script}: no --reload")
        if not needs_reload and "--reload" in body:
            errors.append(f"{script}: unexpected --reload in the production entrypoint")

    if (inst / "Dockerfile.orig").exists():
        errors.append("Dockerfile.orig is still present")

    for error in errors:
        print(f"FAIL  {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
