(ifdd-be-api)=
# API

The backend documents its own HTTP API:

| URL | Content |
|---|---|
| `{{ cookiecutter.ifdd_be_url }}/docs` | Swagger UI: read, sign in, try endpoints |
| `{{ cookiecutter.ifdd_be_url }}/redoc` | ReDoc: the same document for reading, with search |
| `{{ cookiecutter.ifdd_be_url }}/openapi.json` | the OpenAPI 3.1 document |

The document explains the concepts (contexts and their kinds, access with
node roles and context patterns, valid time and system time, the `c_*`
metadata) and describes every endpoint with the role it needs, its
parameters, its error answers and examples. The same content, without a
running backend, is in {ref}`ifdd-be-core-api-http`; the Python API of the
runtime is in {ref}`ifdd-be-core-api-python`.

## Trying endpoints in Swagger UI

1. Open `{{ cookiecutter.ifdd_be_url }}/docs` and click **Authorize**.
2. Under `OAuth2AuthCode` click **Authorize** again: the login page of the
   realm opens in a new window. After the login the window closes itself.
3. Open an endpoint, **Try it out**, **Execute**. The token is sent with
   every request; the answer shows what the backend returns for your roles.

A reload keeps the login until the token expires (30 minutes in the realm of
the template). A token from elsewhere, for example from client credentials,
goes under `BearerToken`.

What "Authorize" needs, and why the pages are open, is described in
{ref}`ifdd-be-security`; if it fails, see {ref}`ifdd-be-troubleshooting`.

## Endpoints for checks

| Endpoint | Token | Answer |
|---|---|---|
| `/version` | none | `{"version": "{{ cookiecutter.ifdd_be_version }}"}` |
| `/prot_version` | any signed-in user | `{"version": "{{ cookiecutter.ifdd_be_version }}_prot"}`; shown by the UI |
| `/whoami` | any valid token | user name, client roles, context patterns |

```bash
TOKEN=...   # an access token
curl --cacert ca.crt -H "Authorization: Bearer $TOKEN" {{ cookiecutter.ifdd_be_url }}/whoami
```

```json
{"preferred_username": "ifdd-demo",
 "client_roles": ["ifdd_nodes_priv", "ifdd_nodes_ro", "ifdd_nodes_rw", "ifdd_public"],
 "context_patterns": ["ifdd.de"]}
```

## Exporting the OpenAPI document

For the HTTP reference in a documentation build, export the document of this
instance (with its own aspects and routers) from the instance directory:

```bash
python -c "import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'))"
```

Write it to a file from Python as above: the backend logs its start to
standard output, so redirecting the output of `print` would mix log lines
into the JSON.
