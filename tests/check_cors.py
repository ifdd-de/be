"""Check that a rendered instance allows exactly the UI origin of a fixture.

    python tests/check_cors.py <fixture.yaml> <rendered instance>

The configured value is known only here, not inside the instance, so a render
that drops or widens it can only be caught here.
"""

import json
import sys
from pathlib import Path

import yaml

TEMPLATE = Path(__file__).resolve().parent.parent


def main(fixture, instance):
    defaults = json.loads((TEMPLATE / "cookiecutter.json").read_text())
    context = yaml.safe_load(Path(fixture).read_text())["default_context"]
    expected = [context.get("ifdd_ui_url", defaults["ifdd_ui_url"])]
    for line in (Path(instance) / ".env").read_text().splitlines():
        if line.startswith("IFDD_CORS_ORIGINS="):
            found = json.loads(line.split("=", 1)[1])
            break
    else:
        found = None
    if found != expected:
        print(f"FAIL  IFDD_CORS_ORIGINS is {found}, expected {expected}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
