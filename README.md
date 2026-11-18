# ifdd-de/be - Backend Service Template

Cookiecutter template for an IFDD JSON-LD backend micro service.
The shared runtime lives in `ifdd-de/be-core` (distribution `ifdd-be-core`,
imported as `ifdd.be.core`).

This template contains the scaffold only: packaging, container build, compose
files, configuration and the extension points. The shared runtime - data model,
CRUD, JSON-LD processing, OIDC, routers and the application factory - lives in
the separate `ifdd-be-core` package and is pulled in as a versioned dependency.

## Why the split

Template files cannot be parsed by an IDE, a linter or a type checker, because
Jinja placeholders make them invalid Python. Keeping shared logic out of the
template restores those tools for the bulk of the code and turns a change to
shared behaviour into a library release instead of a template update applied to
every instance.

No Python file in this template contains a Jinja placeholder.

## Usage

```bash
cruft create --checkout v0.1.0 https://github.com/ifdd-de/be
```

## Variables

Beyond the usual host, port and OIDC values:

| Variable | Purpose |
|---|---|
| `ifdd_be_core_version` | version constraint for the `ifdd-be-core` dependency |
| `ifdd_be_aspects` | JSON mapping of REST path segment to aspect name; no single quote (`.env` holds it in single quotes) |
| `ifdd_be_role_nodes_read` | client role required for reading (nodes, types, scopes, graph data) |
| `ifdd_be_role_nodes_write` | client role required for writing nodes (`PUT`, `PATCH`, `DELETE`) |
| `ifdd_be_role_public` | client role required by `/prot_version` (signed in, no further rights) |
| `ifdd_oidc_realm` | realm URL; access tokens must carry it as issuer (`iss`) |
| `ifdd_context_root` | shared: root of the context names, default `ifdd.de`; the context pattern of the development user when auth is off (`IFDD_CONTEXT_ROOT`) |
| `ifdd_schema_url` | shared: base URL of the schema service; documents are accepted only with a context from below it |
| `ifdd_ui_url` | browser origin of the UI (`scheme://host[:port]`), the only origin CORS allows; shared with the ui and keycloak templates |
| `ifdd_be_enable_versioning` | `y` (default): a write keeps the versions it replaces as history in system time; `n`: it deletes them. Valid-time periods are kept either way (`IFDD_VERSIONING`, see `ifdd-be-core`) |
| `ifdd_be_postgres_image` | PostgreSQL image, default `postgres:18`; ifdd-be-core needs 13 or later (`btree_gist`, `pg_trgm`) |
| `ifdd_be_version` | service version, used in the image tag, `/version` and the OpenAPI document |
| `ifdd_proxy_network` | shared: external Docker network of the proxy, default `proxy-net`; the compose files join it and name it in `traefik.docker.network` |

Roles are client roles of `ifdd_oidc_jwks_audience`
(`resource_access.<audience>.roles` in the access token). Only access tokens
are accepted (claim `typ` = `Bearer`), not ID tokens of the same client.

Client roles with a dot are **context patterns**: base and aspect contexts
need only the node roles, a domain context (`sub1.dom1.ifdd.de`) also needs a
pattern that matches it (`dom1.ifdd.de`, or the root `ifdd.de`). The rules
are described in `ifdd-be-core` ("Contexts and access"). Without a pattern a
client sees no domain context.

## API documentation

`/docs` (Swagger UI), `/redoc` and `/openapi.json` come from `ifdd-be-core`
and are open on purpose; the instance documentation (pages `security` and
`api`) explains why, what "Authorize"
needs (exact redirect URI in the backend client, realm origin in the proxy's
`csp-api-docs`) and how to check a token with `/whoami`.

## Documentation of the instance (`docs/`)

Every instance carries its operating documentation as Sphinx sources in
MyST Markdown, in English (`docs/en`) and German (`docs/de`), with the same
files, labels and headings in both. The pages follow the work around the
service: `index` (purpose, architecture), `setup`, `build-release`,
`operations`, `security`, `troubleshooting`, `reference`, plus `api`.
cookiecutter fills in the values of the instance. The instance README is only
an entry point that links to them.

The pages have no `conf.py` of their own: they are meant to be copied into a
Sphinx project that documents all services. That project needs `myst_parser`
and `sphinxcontrib.plantuml` (PlantUML with Java and Graphviz).
Labels start with `ifdd-be-`; references to
`ifdd-instances-be` (the instance chapter of the meta repository) and
`ifdd-be-core-*` (the API reference of `ifdd-be-core`) resolve only there.

Rules for editing the pages in the template:

- change both languages in the same commit;
- no Jinja syntax in examples (`{{`, `{%`, `{#`); wrap such text in
  `{% raw %}`;
- the placeholder check of the CI greps the rendered instance for the text
  `cookiecutter` followed by a dot; do not write it literally.

`tests/check_docs.py` checks a rendered instance: same files, labels and
headings per level in both languages, every label with the prefix, every
reference to an own label resolvable, and a Sphinx build of each language
with `-W` (configuration `tests/docs/conf.py`, versions
`tests/docs/requirements.txt`).

The check runs PlantUML, so it needs Java and Graphviz.
`tests/docs/get_plantuml.sh` downloads the pinned PlantUML jar into the user
cache, checks its SHA-256 and prints its path:

```bash
export IFDD_PLANTUML_JAR="$(tests/docs/get_plantuml.sh)"
```

## CI

| Workflow | Trigger | Does |
|---|---|---|
| `template-test.yml` | push, PR | renders the template against three fixture configurations, checks CORS (`tests/check_cors.py`), the context root (`tests/check_context_root.py`), the database service and start order (`tests/check_db_service.py`), the image setup (`tests/check_image.py`), that two instances with different project names share no Traefik or image name (`tests/check_two_instances.py`, with a counter-check), that a shell can source the rendered `.env` and that the hook rejects a single quote in `ifdd_be_aspects`, installs the result and runs its tests, and checks and builds its documentation (`tests/check_docs.py`) |
| `template-update-test.yml` | push, PR | generates an instance from the latest tag, applies the current template with `cruft update` and fails on reject files |

A template can be syntactically fine and still fail to render, so the render
step is the one that matters. The update test covers the failure mode a plain
render cannot see: a change that renders cleanly but breaks existing instances.

`template-test.yml` checks out `ifdd-de/be-core` (branch `main`) to install
the runtime, so the template is tested against the current runtime, which may
be ahead of the release on PyPI.

Generated instances carry two workflows of their own: `ci.yml` (tests plus
`cruft check` and `cruft diff` as drift indicators) and `release.yml` (image
build and push to ghcr.io on a `v*` tag).

## AI assistance

Some parts of this repository, in particular the tests, the test data and the
documentation, were developed or improved with the help of large language
models (LLMs). All changes were reviewed and released by the maintainer.
