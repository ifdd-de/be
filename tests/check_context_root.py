"""Check that a rendered instance carries the context root of a fixture.

    python tests/check_context_root.py <fixture.yaml> <rendered instance>

IFDD_CONTEXT_ROOT is the context pattern of the development user; a render
that drops it leaves the default of ifdd-be-core in place unnoticed.
"""

import json
import sys
from pathlib import Path

import yaml

TEMPLATE = Path(__file__).resolve().parent.parent


def main(fixture, instance):
    defaults = json.loads((TEMPLATE / "cookiecutter.json").read_text())
    context = yaml.safe_load(Path(fixture).read_text())["default_context"]
    expected = context.get("ifdd_context_root", defaults["ifdd_context_root"])
    lines = (Path(instance) / ".env").read_text().splitlines()
    found = next((line.split("=", 1)[1] for line in lines
                  if line.startswith("IFDD_CONTEXT_ROOT=")), None)
    if found != expected:
        print(f"FAIL  IFDD_CONTEXT_ROOT is {found!r}, expected {expected!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
