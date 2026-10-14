"""Check the database service of a rendered instance.

    python tests/check_db_service.py <rendered instance>

- The healthcheck names the database (pg_isready -d): without it pg_isready
  connects to a database named like the user, and PostgreSQL logs a failed
  connection attempt at every check.
- Named volumes carry no SELinux relabel option (:z/:Z): that is an option for
  bind mounts, and Docker Compose warns about it on named volumes.
- The backend waits for a healthy database: prestart.sh creates the tables
  before the server starts. Both images copy prestart.sh.
- PostgreSQL comes from ifdd_be_postgres_image, 18 or later, and the volume
  is mounted at /var/lib/postgresql: from 18 on the image keeps its data in
  a versioned subdirectory there, a mount at .../data is wrong.
- .env sets IFDD_VERSIONING (ifdd_be_enable_versioning).
"""

import re
import sys
from pathlib import Path

import yaml


def main(instance):
    errors = []
    for compose_file in ("docker-compose-production.yml", "docker-compose-development.yml"):
        db = yaml.safe_load((Path(instance) / compose_file).read_text())["services"]["db"]
        test = " ".join(db["healthcheck"]["test"])
        if "pg_isready" in test and " -d " not in f"{test} ":
            errors.append(f"{compose_file}: healthcheck without -d: {test}")
        for volume in db.get("volumes", []):
            parts = volume.split(":") if isinstance(volume, str) else []
            named = parts and not parts[0].startswith((".", "/", "~"))
            if named and len(parts) > 2 and set(parts[2].split(",")) & {"z", "Z"}:
                errors.append(f"{compose_file}: SELinux option on named volume: {volume}")
    for compose_file in ("docker-compose-production.yml", "docker-compose-development.yml"):
        backend = yaml.safe_load((Path(instance) / compose_file).read_text())["services"]["backend"]
        condition = (backend.get("depends_on") or {}).get("db", {}).get("condition")
        if condition != "service_healthy":
            errors.append(f"{compose_file}: backend does not wait for a healthy db")
    for compose_file in ("docker-compose-production.yml", "docker-compose-development.yml"):
        db = yaml.safe_load((Path(instance) / compose_file).read_text())["services"]["db"]
        major = re.fullmatch(r"postgres:(\d+)(\D.*)?", str(db.get("image", "")))
        if not major or int(major.group(1)) < 18:
            errors.append(f"{compose_file}: database image is not PostgreSQL 18+: {db.get('image')}")
        targets = [v.split(":")[1] for v in db.get("volumes", []) if isinstance(v, str) and ":" in v]
        if "/var/lib/postgresql" not in targets:
            errors.append(f"{compose_file}: data volume not mounted at /var/lib/postgresql: {targets}")
    dotenv = (Path(instance) / "dotenv.dist").read_text()
    if not re.search(r"^IFDD_VERSIONING=[yn]$", dotenv, re.MULTILINE):
        errors.append("dotenv.dist: IFDD_VERSIONING missing or not y/n")
    prestart = Path(instance) / "prestart.sh"
    if "ifdd-be-create-tables" not in (prestart.read_text() if prestart.exists() else ""):
        errors.append("prestart.sh missing or without ifdd-be-create-tables")
    for dockerfile in ("Dockerfile", "Dockerfile.dev"):
        if "COPY prestart.sh /app/prestart.sh" not in (Path(instance) / dockerfile).read_text():
            errors.append(f"{dockerfile}: does not copy prestart.sh")
    for error in errors:
        print(f"FAIL  {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
