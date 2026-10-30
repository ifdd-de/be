(ifdd-be-setup)=
# Setup

## Prerequisites

| What | Why |
|---|---|
| Docker with Compose | the backend and its database run as two containers |
| the external network `{{ cookiecutter.ifdd_proxy_network }}` and a running proxy instance | Traefik routes `{{ cookiecutter.ifdd_be_host }}` to the backend; the backend reaches Keycloak and the schema service through it |
| the proxy lists `{{ cookiecutter.ifdd_be_host }}`, the Keycloak host and the schema host in `ifdd_proxy_internal_hosts` | inside the containers these names must lead to Traefik, not to the container itself |
| a Keycloak instance with the realm `{{ cookiecutter.ifdd_oidc_realm }}` | issuer and signing keys of the access tokens |
| a schema instance below `{{ cookiecutter.ifdd_schema_url }}` | the JSON-LD contexts of every document written |
| the be-core wheel in `wheels/` while `ifdd-be-core` is not on PyPI | the image installs it from there |
| the CA certificate of the proxy (`certs/ca.crt` there) in `certs/` | the image must trust the proxy's certificate |

## Check the calls through the proxy

The backend fetches the realm's signing keys and the JSON-LD contexts under
their public URLs. From the running container:

```bash
docker compose -f docker-compose-production.yml exec backend python -c \
  "import os, urllib.request; print(urllib.request.urlopen(os.environ['IFDD_OIDC_JWKS_URL'], timeout=5).status)"
```

`200` means that name resolution and certificate are fine. Otherwise see
{ref}`ifdd-be-troubleshooting`.

## Create the instance

Usually the meta repository creates every instance in one go
(`.adm_meta_01_all.sh`, step `.adm_01_create_services.sh`): it runs
`cruft create` with the shared variable file `.cookiecutter_all.yaml`, copies
the be-core wheel into `wheels/` and the CA of the proxy into `certs/`.

By hand, from the directory that holds the instances:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip envs --skip .env \
  https://github.com/ifdd-de/be
cp <be-core>/dist/ifdd_be_core-*.whl {{ cookiecutter.ifdd_be_prj_slug }}/wheels/
cp proxy/certs/ca.crt {{ cookiecutter.ifdd_be_prj_slug }}/certs/
```

Build the wheel from the current source of be-core and remove older wheels of
the same version first: pip takes any wheel with a matching version, and an
image with an old build under the same version number has happened more than
once (see {ref}`ifdd-be-troubleshooting`).

## Configuration and secrets

The post-generation hook writes `.env` from `dotenv.dist` (mode 0600) and
generates two secrets into it: `FASTAPI_SECRET_KEY` and `POSTGRES_PASSWORD`.
`.env` is never committed and never overwritten by a later `cruft update`;
new entries of `dotenv.dist` have to be added to an existing `.env` by hand.

Every other value comes from the variables of the template. They are listed
with their values and meaning in {ref}`ifdd-instances-be`; the ones that
decide how the backend behaves:

| Variable | Value here | Effect |
|---|---|---|
| `ifdd_be_enable_auth` | `{{ cookiecutter.ifdd_be_enable_auth }}` | `y`: every request needs an access token; `n`: development mode without any check |
| `ifdd_be_aspects` | `{{ cookiecutter.ifdd_be_aspects }}` | REST path segments and their aspects (`IFDD_ASPECTS`) |
| `ifdd_be_enable_versioning` | `{{ cookiecutter.ifdd_be_enable_versioning }}` | keep replaced versions as history (`y`) or delete them (`n`) |
| `ifdd_context_root` | `{{ cookiecutter.ifdd_context_root }}` | context pattern of the development user |
| `ifdd_ui_url` | `{{ cookiecutter.ifdd_ui_url }}` | the only browser origin CORS allows |

An aspect is configuration, not code: add it to `IFDD_ASPECTS` in `.env`,
for example `'{"products": "product", "assets": "asset"}'`, and restart.
The single quotes around the JSON (and around `API_TITLE`) keep `.env`
loadable by a shell (`set -a; . ./.env; set +a`); docker compose and the
backend read the value without them. Instances generated before this change
have the values without quotes: add them by hand if you load `.env` in a
shell. A single quote inside these values is not possible.

## Skip list

Paths that belong to the instance and that `cruft update` must not touch:
`.env`, `envs`, `certs`, `app/routers`, `app/settings.py`, `tests`. The
template's `pyproject.toml` lists them under `[tool.cruft]`; pass `.env` and
`envs` with `--skip` when creating the instance, as the meta repository does.

## First start

Production (image built from `Dockerfile`):

```bash
docker compose -f docker-compose-production.yml build
docker compose -f docker-compose-production.yml up -d
curl --cacert ../proxy/certs/ca.crt {{ cookiecutter.ifdd_be_url }}/version
```

The backend waits for a healthy database, then `prestart.sh` creates the
extensions and the table (`ifdd-be-create-tables`) and uvicorn starts.

Development (`Dockerfile.dev`, `start-reload.sh`): `app/` is mounted into
the container and uvicorn reloads on changes; authentication is **off**
(`IFDD_BE_AUTH_ENABLED=false` in `docker-compose-development.yml`), and the
image does not take over the certificates in `certs/`.

```bash
docker compose -f docker-compose-development.yml up --build
```

Without Docker, for work on `app/`:

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```
