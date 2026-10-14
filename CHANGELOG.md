# Changelog

The version scheme follows the other IFDD repositories: `YY.MM.N`.

## [26.10.2] - 2026-10-14

- The backend runs as the unprivileged user `be` (uid/gid 10001) instead of
  root, in `Dockerfile` and `Dockerfile.dev`. The code stays owned by root
  and readable for all; the backend writes no files at run time. The
  security page of the documentation says so. `tests/check_image.py` checks
  that the last `USER` of both Dockerfiles is not root. Existing instances
  get it with `cruft update` and a rebuild of the image; there is nothing to
  migrate.
- Instance test `test_configured_aspect_routes_exist`: reads the paths from
  the OpenAPI document instead of `app.routes`, where included routers have
  no `path` since FastAPI 0.141.1; it failed with every current FastAPI.
  `tests/` is on the skip list: existing instances change the line by hand
  (see the troubleshooting page of the instance documentation).
- `requires-python >=3.13` (was 3.14), so that the instance CI (Python 3.13)
  can install the package.
- `.env`: `IFDD_ASPECTS` and `API_TITLE` in single quotes, so that a shell
  can source the file (`set -a; . ./.env; set +a`); unquoted, the JSON and
  a title with spaces broke the shell. docker compose and pydantic-settings
  read the same values. The pre-generation hook rejects a single quote in
  `ifdd_be_aspects` and `ifdd_be_prj_name`. `.env` belongs to the instance:
  existing instances add the quotes by hand if needed. Template CI sources
  the rendered `.env` and checks the hook.
- API documentation: the instance README describes `/docs`, `/redoc` and
  `/openapi.json` of `ifdd-be-core`: open on purpose (they hold no data),
  what "Authorize" needs (redirect URI `<be url>/docs/oauth2-redirect` in the
  backend client, the realm origin in the proxy's `csp-api-docs`), `/whoami`
  for 403 answers. Existing realms keep `<be url>/*` until it is changed in
  the admin console.
- Production compose file: the comment on `csp-api-docs` no longer says to
  switch to `csp-api` once `/docs` is disabled; `/docs` stays.
- Smoke test of new instances: the documentation pages and their assets are
  served (`tests/` is on the skip list, existing instances keep theirs).
- Documentation of the instance in `docs/en` and `docs/de` (Sphinx sources,
  MyST Markdown): index, setup, build and release, operations, security,
  troubleshooting, reference, API. The instance README is now an entry point
  with a quick start, the links, the honesty notes and the license; its
  former sections moved into the documentation.
- `docs/` in `.dockerignore`, `docs/_build/` in `.gitignore` of the instance.
- Template CI: `tests/check_docs.py` checks that both languages match and
  build without warnings (`tests/docs/conf.py`, `tests/docs/requirements.txt`).
- This changelog.
