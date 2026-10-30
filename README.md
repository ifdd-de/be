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
and `sphinxcontrib.mermaid`. Labels start with `ifdd-be-`; references to
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

## CI

| Workflow | Trigger | Does |
|---|---|---|
| `template-test.yml` | push, PR | renders the template against three fixture configurations, checks CORS (`tests/check_cors.py`), the context root (`tests/check_context_root.py`), the database service and start order (`tests/check_db_service.py`), the image setup (`tests/check_image.py`), that a shell can source the rendered `.env` and that the hook rejects a single quote in `ifdd_be_aspects`, installs the result and runs its tests, and checks and builds its documentation (`tests/check_docs.py`) |
| `template-update-test.yml` | push, PR | generates an instance from the latest tag, applies the current template with `cruft update` and fails on reject files |

A template can be syntactically fine and still fail to render, so the render
step is the one that matters. The update test covers the failure mode a plain
render cannot see: a change that renders cleanly but breaks existing instances.

`template-test.yml` checks out `ifdd-de/be-core` to install the runtime. While
that repository is private the job needs a token with read access; once
`ifdd-be-core` is on PyPI the checkout step can be dropped.

Generated instances carry two workflows of their own: `ci.yml` (tests plus
`cruft check` and `cruft diff` as drift indicators) and `release.yml` (image
build and push to ghcr.io on a `v*` tag).

## Honesty notes

See the instance README for CORS, the CA certificates and the calls through
the proxy. `tests/check_cors.py` fails against the template before
`ifdd_ui_url` was introduced (checked).

Database service (2026-10-05): `tests/check_db_service.py` fails against the
previous template (healthcheck without `-d`, `:Z`/`:z` on named volumes) and
passes now; `docker compose config` (Compose v5.5.1) accepts both compose
files and renders the check as `pg_isready -U <user> -d <database>`. Not
observed: the healthcheck running in Docker (no Docker available) and the
Compose warning disappearing; `docker compose config` does not print that
warning, it appeared at `up` in the reported run. The reported symptom was a
`FATAL: database "<user>" does not exist` every 10 seconds.

Start order (2026-10-05): `tests/check_db_service.py` also checks that the
backend waits for a healthy database and that both images copy
`prestart.sh`; it fails against the previous template.

Base image (2026-10-05): the backend uses `python:3.14-slim` and starts
uvicorn directly (no gunicorn). `tests/check_image.py` fails against the
previous template (tiangolo base image, gunicorn).

PostgreSQL 18 and versioning (2026-10-06): the database image comes from
`ifdd_be_postgres_image` (default `postgres:18`, was a fixed `postgres:17`)
and the volume is mounted at `/var/lib/postgresql`, as the 18 image expects
and as the keycloak and wf templates do; `ifdd_be_enable_versioning` sets
`IFDD_VERSIONING`. `tests/check_db_service.py` fails against the previous
template (fixed image, mount at `.../data`, no `IFDD_VERSIONING`); rendered
with cookiecutter 2.7.1 and checked with `docker compose config` (v5.5.1).
`ifdd-be-core` with the bitemporal storage (be-core-3/-4) was tested against
PostgreSQL 18.4. Not checked: the `postgres:18` image itself and what it does
when it finds data of version 17 in the volume.

Documentation `docs/` (2026-10-13): rendered with cookiecutter 2.7.1 for all
three fixtures; `tests/check_docs.py` passes for each (Sphinx 9.1.0,
myst-parser 5.1.0, sphinxcontrib-mermaid 2.1.1, Python 3.13), and the
placeholder check finds nothing. Counter-checks on a rendered copy: a heading
of another level in one language, a reference to an unknown own label, a
label without prefix, an unknown directive in one language and a page in one
language only each make it fail. The workflow file passes actionlint 1.7.12;
the workflow itself has not run. Content: taken from the previous instance
README, the template README, `ifdd-be-core` and the handover notes; what has
not been tested is marked as such in the pages (backup and restore, image
build, resource values). Also checked (2026-10-13): one Sphinx project per language with the pages
of all ten service templates (rendered with `cookiecutter_all.yaml`), the
instance chapter of the meta repository and ifdd-be-core with its OpenAPI
document builds with `-W` and no suppressed warnings, so every cross
reference resolves; the Mermaid diagrams render in headless Chromium
141.0.7390.37 (Playwright 1.56.0, Mermaid 11.12.1 served locally).

API documentation (2026-10-13): the instance README has a new section, the
production compose file a corrected comment on `csp-api-docs`, and the smoke
test of new instances checks the documentation pages. Rendered with
cookiecutter 2.7.1 (all three fixtures); the rendered instance installed with
the changed `ifdd-be-core`: the new smoke test passes and fails with the
previous `ifdd-be-core`; the known route test still fails as before.

Context access (2026-10-12): `ifdd_context_root` renders to
`IFDD_CONTEXT_ROOT`; `tests/check_context_root.py` checks it for all three
fixtures (rendered with cookiecutter 2.7.1) and fails against the previous
template. The rendered instance was installed with the changed `ifdd-be-core`
(be-core-5): its smoke test passes, the known route test
(`test_configured_aspect_routes_exist`) still fails as before. Existing
instances: add `IFDD_CONTEXT_ROOT` to `.env` by hand (`.env` is on the skip
list), drop the `nodes` table and load the data again (new column `domain`).
Not checked: the image build.

`.env` loadable by a shell (2026-10-13): rendered with cookiecutter 2.7.1
(all three fixtures and the `cookiecutter_all.yaml` of the meta repository).
`set -a; . ./.env; set +a` in bash 5.2.21 runs without an error and leaves
valid JSON in `IFDD_ASPECTS`; before, it failed at `API_TITLE` (a title
with spaces) and at the JSON. `CoreSettings` of ifdd-be-core
(pydantic-settings 2.15.0) and `docker compose config` (v5.5.1, `env_file`)
read both values without the quotes. The hook rejects a single quote in
`ifdd_be_aspects`; both checks fail against the previous template. The
instance tests are unchanged (the known route test still fails). The
workflow passes actionlint 1.7.12; it has not run.

Route test and Python 3.13 (2026-10-13): `test_configured_aspect_routes_exist`
takes the paths from `app.openapi()`. With FastAPI 0.142.4 and the changed
ifdd-be-core, on Python 3.13.16 and 3.14.6, the instance tests pass (3 of 3)
for all three fixtures; the old line fails with the same FastAPI, and the new
test fails when a configured segment has no route. `requires-python >=3.13`:
installing the rendered instance on Python 3.13.16 works. Not checked: the
instance CI itself, which also needs ifdd-be-core from PyPI or `wheels/`.
