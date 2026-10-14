(ifdd-be-build-release)=
# Build and release

## Images

| File | Image | Use |
|---|---|---|
| `Dockerfile` | `{{ cookiecutter.ifdd_registry_url }}/{{ cookiecutter.ifdd_be_prj_slug }}:{{ cookiecutter.ifdd_be_version }}` | production |
| `Dockerfile.dev` | built by `docker-compose-development.yml` | development with auto-reload |

Both start from `python:3.14-slim` and start uvicorn directly (no gunicorn)
with the app factory of `ifdd-be-core`. The production image

1. installs the instance and `ifdd-be-core` with `pip install --find-links /tmp/wheels`,
   so a wheel in `wheels/` wins over the package index;
2. adds every `*.crt` and `*.pem` of `certs/` to the system trust store and
   points `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` at it (token keys and
   JSON-LD contexts are fetched over HTTPS);
3. checks itself with a health check on `/version` (Python, no curl in the
   image).

```bash
docker compose -f docker-compose-production.yml build     # one instance
./.adm_02_build_services.sh production                    # all, from the meta repository
```

Rebuild after every change of `wheels/`, `certs/` or `app/`: the image takes
them over at build time.

## The be-core wheel

While `ifdd-be-core` is not published on PyPI, the image installs it from
`wheels/`:

1. build the wheel from the current source of be-core (`python -m build` or
   `uv build` there);
2. remove older wheels of the same version from `wheels/`;
3. copy the new one and rebuild the image.

Without step 2 the image may contain an old build under the same version
number. `/openapi.json` names the be-core version in its description; it
does not tell two builds of the same version apart.

## Versions

| Value | Here | Source |
|---|---|---|
| version of the instance | `{{ cookiecutter.ifdd_be_version }}` | template variable `ifdd_be_version`; image tag, `/version`, OpenAPI document |
| be-core dependency | `~={{ cookiecutter.ifdd_be_core_version }}` | template variable `ifdd_be_core_version`, in `pyproject.toml` |

The scheme is `YY.MM.N` (26.10.1 is the first version in October 2026). Both
values come from the template, not from `.cookiecutter_all.yaml`, so a new
template version brings them with `cruft update`.

## CI of the instance

`.github/workflows/ci.yml` runs on every push and pull request:

- **test**: installs the instance with its dev extras and runs `pytest`;
- **template drift**: `cruft check` and `cruft diff`, both informational
  (they do not fail the run). What `cruft diff` shows either belongs back into
  the template or on the skip list.

## Release

`.github/workflows/release.yml` builds the production image and pushes it to
`ghcr.io/<owner>/<repository>` when a tag `v*` is pushed (tags from the tag
name, the version and the commit). It uses the `GITHUB_TOKEN` of the run; no
other secret is needed. The local image name above
(`{{ cookiecutter.ifdd_registry_url }}/...`) is independent of it.

```{note}
Not tested: the release workflow on GitHub, and the image build itself
(the template tests render and install the instance without Docker).
```
