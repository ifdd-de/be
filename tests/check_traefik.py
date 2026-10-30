"""Check the Traefik labels of a rendered instance.

    python tests/check_traefik.py <fixture.yaml> <rendered instance>

- Every router, service and middleware the labels declare is named after the
  project slug (the slug itself or the slug followed by "-"), so that two
  instances behind one proxy do not declare the same names. The slug is the
  name of the rendered directory.
- traefik.docker.network and the external network the service joins are
  ifdd_proxy_network of the fixture (or the template default).
"""

import json
import re
import sys
from pathlib import Path

import yaml

TEMPLATE = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^traefik\.http\.(routers|services|middlewares)\.([^.]+)\.")


def labels_of(service):
    labels = service.get("labels") or []
    if isinstance(labels, dict):
        return [f"{key}={value}" for key, value in labels.items()]
    return labels


def main(fixture, instance):
    defaults = json.loads((TEMPLATE / "cookiecutter.json").read_text())
    context = yaml.safe_load(Path(fixture).read_text())["default_context"]
    network = context.get("ifdd_proxy_network", defaults["ifdd_proxy_network"])
    slug = Path(instance).resolve().name
    errors = []
    for compose_file in ("docker-compose-production.yml", "docker-compose-development.yml"):
        compose = yaml.safe_load((Path(instance) / compose_file).read_text())
        for service_name, service in compose["services"].items():
            labels = labels_of(service)
            if "traefik.enable=true" not in labels:
                continue
            for label in labels:
                match = NAME.match(label)
                if match and not (match[2] == slug or match[2].startswith(slug + "-")):
                    errors.append(f"{compose_file}: {service_name}: {match[1]} name "
                                  f"{match[2]!r} is not the slug {slug!r}: {label}")
            if f"traefik.docker.network={network}" not in labels:
                errors.append(f"{compose_file}: {service_name}: no traefik.docker.network={network}")
            joined = {compose["networks"][key].get("name")
                      for key in service.get("networks") or []
                      if (compose.get("networks") or {}).get(key, {}).get("external")}
            if network not in joined:
                errors.append(f"{compose_file}: {service_name}: does not join the external "
                              f"network {network!r} (joins {sorted(joined)})")
    for error in errors:
        print(f"FAIL  {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
