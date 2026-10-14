# {{cookiecutter.ifdd_be_prj_name}}

The JSON-LD backend of an IFDD node, generated from the template `ifdd-de/be`.
The runtime is the package `ifdd-be-core`; this repository holds the frame:
packaging, image, compose files, configuration (`.env`) and the extension
points `app/settings.py` and `app/routers/`.

## Quick start

```bash
cp <be-core>/dist/ifdd_be_core-*.whl wheels/   # while ifdd-be-core is not on PyPI
cp <proxy instance>/certs/ca.crt certs/         # trust the proxy's certificate
docker compose -f docker-compose-production.yml up -d --build
curl --cacert certs/ca.crt {{cookiecutter.ifdd_be_url}}/version
```

The API is documented at `{{cookiecutter.ifdd_be_url}}/docs` (Swagger UI) and
`{{cookiecutter.ifdd_be_url}}/redoc`.

## Documentation

Setup, build and release, operations, security, troubleshooting, reference
and API of this instance:

- English: [docs/en/index.md](docs/en/index.md)
- Deutsch: [docs/de/index.md](docs/de/index.md)

The pages are Sphinx sources in MyST Markdown, meant to be copied into a
documentation project that covers all services; GitHub shows them as plain
Markdown.

## Honesty notes

CORS, CA certificates and calls through the proxy (2026-10-04):

- Rendering with cookiecutter 2.7.1: `IFDD_CORS_ORIGINS` holds exactly
  `ifdd_ui_url` (`tests/check_cors.py` in the template; it fails against the
  previous template). `docker compose config` (Compose v5.5.1) accepts both
  compose files.
- End to end, without Docker: the real Traefik v3.7.13 binary with the
  rendered production configuration (file provider instead of the Docker
  labels, routers with the same rules), the certificate of `adm_01_certs.sh`
  from the proxy template, the real Keycloak 26.8.0 distribution with the
  realm of the keycloak template, be-core 26.10.2 with the authentication
  changes, and the authorization code flow with PKCE as the UI runs it.
  Observed:
  - with the CA added to the system store as in the `Dockerfile` and both
    variables set: the access token is accepted through the proxy, a user
    without group gets 403 on reads, a reader passes the role check, the
    preflight from the UI origin gets 200 and from another origin 400, and the
    JSON-LD loader fetches a context from `https://<schema host>`;
  - without the CA: 401 "Unable to verify token signature ...
    CERTIFICATE_VERIFY_FAILED", and the context cannot be fetched;
  - with the CA in the system store but without `REQUESTS_CA_BUNDLE`: token
    validation works, the JSON-LD context does not (requests uses its own
    certifi bundle). Hence both variables.
- Not verified: the image build (no container registry was reachable),
  including `update-ca-certificates` in `python:3.14-slim`, whose Debian base
  installs `ca-certificates`. Name resolution through the Docker network
  aliases of the proxy.

`prestart.sh` (2026-10-05): run the way the base image's start script runs
it (sourced by `sh` under `set -e`; read in its published `start.sh`)
against PostgreSQL 16: it creates the table, a second run changes nothing,
and with the database down the start stops with exit code 1. Not run inside
the image (no Docker available).

API documentation (2026-10-13): `/docs`, `/redoc` and `/openapi.json` come
from `ifdd-be-core` (its README has the tests: headless Chromium behind
Traefik v3.7.13 with the rendered proxy configuration and the Keycloak 26.8.0
distribution with the rendered realm). `tests/test_smoke.py` checks that the
pages and their assets are served by the installed package; it fails with
the previous `ifdd-be-core`. `tests/` is on the skip list: existing instances
keep their old smoke test. Not checked: the admin console steps for an
existing realm, and the image.

Base image and startup (2026-10-05): the backend runs on `python:3.14-slim`
and starts uvicorn directly (no gunicorn, no tiangolo base image); `start.sh`
runs `prestart.sh` and then `uvicorn --factory ifdd.be.core:create_app`
with `WORKERS` processes, `start-reload.sh` the same with `--reload`. Checked
without Docker: rendering with cookiecutter 2.7.1, `tests/check_image.py`
(fails against the previous template), `docker compose config` (Compose
v5.5.1), and the start path against PostgreSQL 16 (prestart creates the table,
uvicorn serves `/version` with 200, two workers run, the healthcheck line
returns 0). Not checked: the image build itself and whether every dependency
has a cp314 wheel there (checked on PyPI, not in the image).

Unprivileged container user (2026-10-14): both Dockerfiles create the user
`be` (uid/gid 10001) and end with `USER be`; `tests/check_image.py` in the
template fails without it (checked against the previous template). The
`groupadd`/`useradd` options were tried with shadow 4.13 (Ubuntu 24.04)
against a scratch root. Not verified, because no Docker daemon was available:
the image build itself, which shadow version `python:3.14-slim` ships and
whether it has `/usr/sbin/nologin` (a missing shell is only a warning in
4.13), and the running container (`docker compose exec backend id`, start,
health check, token validation with the system CA store as `be`).

## License

BSD-3-Clause, see `LICENSE`.
