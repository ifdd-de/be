import re
import sys

PROJECT_SLUG_REGEX = r'^[_a-zA-Z][_a-zA-Z0-9-]+$'

ifdd_be_prj_slug = '{{ cookiecutter.ifdd_be_prj_slug }}'

if not re.match(PROJECT_SLUG_REGEX, ifdd_be_prj_slug):
    print('ERROR: %s is not a valid Python module name!' % ifdd_be_prj_slug)

    # exits with status 1 to indicate failure
    sys.exit(1)

# The browser origin of the UI, the only origin allowed by CORS. Browsers send
# it as scheme://host[:port], without path and without the default port, and
# the backend compares it character by character.
ORIGIN_REGEX = r'^(https?)://[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:([0-9]{1,5}))?$'
DEFAULT_PORTS = {'http': '80', 'https': '443'}

ifdd_ui_url = '{{ cookiecutter.ifdd_ui_url }}'
origin = re.match(ORIGIN_REGEX, ifdd_ui_url)
if not origin or origin.group(4) == DEFAULT_PORTS[origin.group(1)]:
    print('ERROR: ifdd_ui_url must be a browser origin such as https://ui.example.org '
          '(no path, no trailing slash, no default port), got %r' % ifdd_ui_url)
    sys.exit(1)

# .env holds these values in single quotes, so that a shell can source it.
for name, value in (
    ("ifdd_be_prj_name", r"""{{ cookiecutter.ifdd_be_prj_name }}"""),
    ("ifdd_be_aspects", r"""{{ cookiecutter.ifdd_be_aspects }}"""),
):
    if "'" in value:
        print("ERROR: %s must not contain a single quote (')" % name)
        sys.exit(1)
