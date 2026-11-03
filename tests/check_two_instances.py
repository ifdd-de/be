"""Check that two instances can run on the same Docker host.

    python tests/check_two_instances.py <instance A> <instance B>

Two instances of this template on one server (for example two stages on one
virtual machine) share the Docker host, its image store and the Traefik of
its proxy. They must not share a Traefik router, service or middleware name
(Traefik refuses or mixes up duplicates) nor an image name (the second build
would replace the first one, with the other instance's configuration).
Both follow the project name, so the two instances need different ones.
Exit code 1 lists every shared name.
"""

import re
import sys
from pathlib import Path

import yaml

COMPOSE_FILES = ("docker-compose-production.yml", "docker-compose-development.yml")
TRAEFIK = re.compile(r"^traefik\.http\.(routers|services|middlewares)\.([^.]+)\.")


def names(instance):
    found = set()
    for compose_file in COMPOSE_FILES:
        path = Path(instance) / compose_file
        if not path.is_file():
            continue
        for service in (yaml.safe_load(path.read_text())["services"] or {}).values():
            for label in service.get("labels") or []:
                match = TRAEFIK.match(label)
                if match:
                    found.add(f"traefik {match[1]} {match[2]}")
            if "image" in service and "build" in service:
                found.add(f"image {service['image']}")
    return found


def main(first, second):
    shared = sorted(names(first) & names(second))
    for name in shared:
        print(f"FAIL  both instances use the {name}")
    return 1 if shared else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
