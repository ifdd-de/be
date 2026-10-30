(ifdd-be-reference)=
# Reference

The template variables of this instance, with their values and meaning, are
in {ref}`ifdd-instances-be`. This page lists what is not a template variable.

## Environment (`.env`)

Generated from `dotenv.dist`; the backend reads it through pydantic-settings
and ignores unknown names.

| Name | Here | Meaning |
|---|---|---|
| `MAX_WORKERS` | `{{ cookiecutter.ifdd_be_max_workers }}` | uvicorn processes (`WORKERS` in the container) |
| `LOG_LEVEL` | `{{ cookiecutter.ifdd_be_log_level.upper() }}` | log level |
| `FORWARDED_ALLOW_IPS` | `*` | addresses whose `X-Forwarded-*` headers uvicorn trusts |
| `FASTAPI_SECRET_KEY` | generated | key of the session middleware |
| `API_TITLE` | `{{ cookiecutter.ifdd_be_prj_name }}` | title of the OpenAPI document and the documentation pages |
| `IFDD_BE_VERSION` | `{{ cookiecutter.ifdd_be_version }}` | version shown by `/version`, `/prot_version` and the OpenAPI document |
| `IFDD_BE_PORT` | `{{ cookiecutter.ifdd_be_port }}` | internal port; the compose files pass it to the container as `PORT` |
| `IFDD_BE_HOST` | `{{ cookiecutter.ifdd_be_host }}` | host for `python -m app.main` only |
| `IFDD_BE_URL` | `{{ cookiecutter.ifdd_be_url }}` | public URL; not read by `ifdd-be-core`, kept for people and scripts |
| `IFDD_BE_AUTH_ENABLED` | `{{ cookiecutter.ifdd_be_enable_auth }}` | check tokens |
| `IFDD_VERSIONING` | `{{ cookiecutter.ifdd_be_enable_versioning }}` | keep replaced versions as history |
| `IFDD_BE_SSL_ENABLED` | `{{ cookiecutter.ifdd_be_enable_tls }}` | session cookie only over HTTPS (follows the deprecated `ifdd_be_enable_tls`) |
| `IFDD_TYPE_URL`, `IFDD_SCHEMA_URL` | `{{ cookiecutter.ifdd_type_url }}`, `{{ cookiecutter.ifdd_schema_url }}` | vocabularies; contexts are accepted only from below the schema URL |
| `IFDD_ASPECTS` | `{{ cookiecutter.ifdd_be_aspects }}` | REST path segment to aspect |
| `IFDD_ROLE_NODES_READ`, `IFDD_ROLE_NODES_WRITE`, `IFDD_ROLE_PUBLIC` | `{{ cookiecutter.ifdd_be_role_nodes_read }}`, `{{ cookiecutter.ifdd_be_role_nodes_write }}`, `{{ cookiecutter.ifdd_be_role_public }}` | node roles |
| `IFDD_CONTEXT_ROOT` | `{{ cookiecutter.ifdd_context_root }}` | context pattern of the development user |
| `IFDD_CORS_ORIGINS` | `["{{ cookiecutter.ifdd_ui_url }}"]` | allowed browser origins |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` | `{{ cookiecutter.ifdd_be_postgres_host }}`, `{{ cookiecutter.ifdd_be_postgres_port }}`, `{{ cookiecutter.ifdd_be_postgres_db }}`, `{{ cookiecutter.ifdd_be_postgres_user }}` | database |
| `POSTGRES_PASSWORD` | generated | database password |
| `IFDD_SERVICE_DB_URL` | built from the `POSTGRES_*` values | connection URL (`postgresql+psycopg://...`) |
| `IFDD_OIDC_TOKEN_URL`, `IFDD_OIDC_AUTHORIZATION_URL`, `IFDD_OIDC_REFRESH_URL` | endpoints of the realm | login of Swagger UI |
| `IFDD_OIDC_JWKS_URL` | `{{ cookiecutter.ifdd_oidc_jwks_url }}` | signing keys |
| `IFDD_OIDC_JWKS_AUDIENCE` | `{{ cookiecutter.ifdd_oidc_jwks_audience }}` | required audience; client of the roles |
| `IFDD_OIDC_ISSUER` | `{{ cookiecutter.ifdd_oidc_realm }}` | required issuer |
| `IFDD_OIDC_JWKS_ALGORITHM` | `{{ cookiecutter.ifdd_oidc_jwks_algorithm }}` | signature algorithm |

`MODULE_NAME` and `ACCESS_LOG` are left over from the former base image and
have no effect.

Further settings of `ifdd-be-core` with defaults, settable in `.env`:
`JSONLD_CACHE_EXPIRE_AFTER` (120 s), `JSONLD_LOADER_TIMEOUT` (10 s),
`IFDD_TOKEN_CACHE_SIZE` (1000), `IFDD_TOKEN_CACHE_TTL` (300 s),
`IFDD_DB_POOL_SIZE` (20), `IFDD_DB_MAX_OVERFLOW` (0),
`IFDD_DB_POOL_TIMEOUT` (30 s), `IFDD_GRAPH_PREDICATES`,
`IFDD_GRAPH_MAX_DEPTH` (4), `API_SUMMARY`.

## Ports, networks, volumes

| Kind | Name | Note |
|---|---|---|
| port | `{{ cookiecutter.ifdd_be_port }}` | uvicorn inside the networks; not published on the host |
| network | `{{ cookiecutter.ifdd_proxy_network }}` (external) | Traefik reaches the backend; the backend reaches Keycloak and schema |
| network | `db-net` (internal to the compose project) | backend and database |
| volume | `ifdd_be_postgres_data` | database, at `/var/lib/postgresql` |
| volume | `ifdd_be_postgres_data_backups` | at `/backups` in the database container |

The database is reachable only in `db-net`; no port is published.

## Files

| Path | Purpose |
|---|---|
| `app/main.py` | entry point: `create_app(settings, extra_routers=instance_routers)` |
| `app/settings.py` | instance settings, a subclass of `CoreSettings` (skip list) |
| `app/routers/` | endpoints of this instance only (skip list) |
| `certs/` | CA certificates for the image (git-ignored, skip list) |
| `wheels/` | local wheels, e.g. be-core (build artefacts) |
| `prestart.sh`, `start.sh`, `start-reload.sh` | container start: create tables, then uvicorn |
| `docker-compose-production.yml`, `docker-compose-development.yml` | compose files |
| `dotenv.dist`, `.env` | configuration template and configuration |
| `docs/en`, `docs/de` | this documentation |

## Endpoints

All endpoints with parameters, answers and examples are in the OpenAPI
document (`{{ cookiecutter.ifdd_be_url }}/docs`) and in
{ref}`ifdd-be-core-api-http`. In short:

| Endpoint | Role | Purpose |
|---|---|---|
| `GET`, `POST /{segment}` | read | list of an aspect; `POST` with `{"ids": [...]}` |
| `GET /{segment}/{id}` | read (+ pattern) | one document, all visible contexts |
| `PUT`, `PATCH /{segment}/{id}` | write (+ pattern) | write for a valid time |
| `DELETE /{segment}/{id}` | write (+ pattern) | end the validity |
| `GET /nodes/` | read | documents of every aspect |
| `GET`, `POST /types`, `/scopes` | read | `objType`, `objScope` values in use |
| `POST /graph_data` | read | relations as graph elements |
| `GET /version` | none | version |
| `GET /prot_version` | public | version, for the UI |
| `GET /whoami` | any token | roles and patterns of the token |
| `/docs`, `/redoc`, `/openapi.json` | none | documentation |

The segments of this instance: `{{ cookiecutter.ifdd_be_aspects }}`.
