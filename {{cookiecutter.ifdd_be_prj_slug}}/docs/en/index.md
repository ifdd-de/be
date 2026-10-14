(ifdd-be-index)=
# {{ cookiecutter.ifdd_be_prj_name }} (be)

The backend of an IFDD node: it stores the JSON-LD documents of its domains,
answers with them, and checks every request against the access token of the
realm. This chapter describes the instance `{{ cookiecutter.ifdd_be_prj_slug }}`,
generated from the template `ifdd-de/be`, from the point of view of the
people who set it up, build, run and secure it.

| | |
|---|---|
| Public URL | `{{ cookiecutter.ifdd_be_url }}` (host `{{ cookiecutter.ifdd_be_host }}`, routed by the proxy) |
| Internal port | `{{ cookiecutter.ifdd_be_port }}` (uvicorn, not published) |
| Instance version | `{{ cookiecutter.ifdd_be_version }}` |
| Runtime | package `ifdd-be-core` `~={{ cookiecutter.ifdd_be_core_version }}` |
| Database | PostgreSQL, image `{{ cookiecutter.ifdd_be_postgres_image }}` |
| Realm | `{{ cookiecutter.ifdd_oidc_realm }}`, audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` |

## What the instance contains

The template is only a frame. The runtime (data model, bitemporal storage,
JSON-LD processing, token checks, routers, documentation pages) is the
package `ifdd-be-core`, installed into the image as a versioned dependency.
The instance adds packaging, the container build, the compose files, the
configuration (`.env`) and two extension points: `app/settings.py` for own
settings and `app/routers/` for own endpoints.

## Architecture

```{mermaid}
flowchart LR
  Browser -->|HTTPS| Proxy[proxy: Traefik]
  UI[ui] -->|reads| Proxy
  CT[ct] -->|writes| Proxy
  TS[ts: Grafana] -->|reads| Proxy
  Proxy -->|"{{ cookiecutter.ifdd_be_host }}"| BE[be: uvicorn]
  BE -->|SQL| DB[(PostgreSQL)]
  BE -->|signing keys JWKS| Proxy
  BE -->|JSON-LD contexts| Proxy
  Proxy --> KC[Keycloak]
  Proxy --> Schema[schema]
```

The backend calls two services itself, both under their public URLs through
the proxy: Keycloak for the keys that sign the access tokens, and the schema
service for the JSON-LD contexts of the documents. Inside the proxy network
those host names lead to Traefik (network aliases of the proxy instance), and
the image trusts the proxy's certificate (see {ref}`ifdd-be-setup`).

| Who | Calls the backend for |
|---|---|
| ui | lists and single documents, the version on its dashboard (`/prot_version`) |
| ct | writing documents (PUT) with client credentials |
| ts (Grafana) | reading the objects next to their time series |
| wf (notebooks) | reading, e.g. counting documents |
| people | Swagger UI and ReDoc (`/docs`, `/redoc`) |

The backend never resolves IRIs of other nodes and depends on no other
backend: linking across nodes is up to the clients.

## Chapters

```{toctree}
:maxdepth: 2

setup
build-release
operations
security
troubleshooting
reference
api
```

The values of the variables of this instance and how they relate to the
other services are listed in the chapter on the service instances
({ref}`ifdd-instances-be`).
