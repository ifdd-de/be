(ifdd-be-security)=
# Security

## Authentication

With `IFDD_BE_AUTH_ENABLED=true` every endpoint except `/version` and the
documentation pages needs an OIDC access token of the realm
`{{ cookiecutter.ifdd_oidc_realm }}` (`Authorization: Bearer <token>`). The
backend checks

- the signature against the realm's keys (`IFDD_OIDC_JWKS_URL`, fetched
  through the proxy),
- the expiry,
- the audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` (`IFDD_OIDC_JWKS_AUDIENCE`),
- the issuer `IFDD_OIDC_ISSUER` (set from `ifdd_oidc_realm`; if empty, it is
  not checked and a warning is logged once),
- the token type: only access tokens (`typ` = `Bearer`), never ID tokens of
  the same client (RFC 9068).

A failed check answers 401 with the reason.

Browsers (the UI, Swagger UI) sign in with the authorization code flow and
PKCE; scripts and services (ct, ts, notebooks) use client credentials of
their own confidential clients. The backend accepts both, as long as the
access token carries the roles.

## Authorization

Roles are client roles of `{{ cookiecutter.ifdd_oidc_jwks_audience }}`
(`resource_access.{{ cookiecutter.ifdd_oidc_jwks_audience }}.roles`); people get
them through groups in Keycloak.

| Role | Here | Allows |
|---|---|---|
| public | `{{ cookiecutter.ifdd_be_role_public }}` | `/prot_version` |
| read | `{{ cookiecutter.ifdd_be_role_nodes_read }}` | every read endpoint |
| write | `{{ cookiecutter.ifdd_be_role_nodes_write }}` | PUT, PATCH, DELETE |

Base and aspect contexts need only these roles. A **domain context** (a
dotted name such as `breaker.grid.example.ifdd.de`) also needs a **context
pattern**: a client role with a dot that matches the context name or a name
above it, at label boundaries. `{{ cookiecutter.ifdd_context_root }}` matches every domain
context. Without a pattern a client sees no domain context. Foreign contexts
answer **403, not 404**: their existence is not hidden. `/whoami` shows the
roles and patterns the backend reads from a token.

## Development mode

With `IFDD_BE_AUTH_ENABLED=false` nothing is checked: every request acts as
a development user with all node roles and the pattern
`{{ cookiecutter.ifdd_context_root }}`. `docker-compose-development.yml` switches
authentication off **and** puts the backend behind Traefik under
`{{ cookiecutter.ifdd_be_host }}`: whoever reaches the proxy can read and write
everything. Run the development setup only on a machine that nobody else
can reach.

## Secrets

| Secret | Where | Used for |
|---|---|---|
| `POSTGRES_PASSWORD` | `.env` (generated, mode 0600) | the database user `{{ cookiecutter.ifdd_be_postgres_user }}` |
| `FASTAPI_SECRET_KEY` | `.env` (generated) | signing the session cookie of the session middleware |

Neither is a template variable, so neither ends up in `.cruft.json`. The
database keeps the password it was created with: changing it in `.env` alone
locks the backend out.

## TLS and certificates

The backend speaks plain HTTP on port `{{ cookiecutter.ifdd_be_port }}` inside the
Docker networks; TLS ends at Traefik. For its own calls to Keycloak and the
schema service it uses HTTPS and trusts the system store of the image plus
the CAs in `certs/` (see {ref}`ifdd-be-build-release`). Router labels carry
no `tls` settings: a router with its own TLS section would replace the TLS
configuration of the proxy's entry point.

## Container user

The backend runs as the unprivileged user `be` (uid and gid 10001), not as
root, in the production and the development image. The code belongs to root
and is only readable for `be`. The backend writes no files at run time (its
caches are in memory), so it needs no writable directory or volume. A port
below 1024 for `ifdd_be_port` may not be allowed for this user, depending on
the Docker version; the default `{{ cookiecutter.ifdd_be_port }}` is not
affected. In development the mounted `app/` must be readable for others on
the host.

## Browser protection

- **CORS**: `IFDD_CORS_ORIGINS` allows exactly the UI origin
  `{{ cookiecutter.ifdd_ui_url }}`. The preflight of any other origin is refused
  (`400 Disallowed CORS origin`), so the browser never sends the request with
  the token. For local UI development add its origin to `.env`.
- **Security headers**: the proxy attaches `security-headers` (nosniff,
  frame options, referrer policy, no `Server` header) and the CSP
  `csp-api-docs`.
- **CSP of the documentation pages**: scripts and styles from this host
  only; the realm origin in `connect-src` for "Authorize"; `blob:` workers
  and inline styles for ReDoc. The exact policy is in the README of
  `ifdd-be-core`.

## Open API documentation

`/docs`, `/redoc` and `/openapi.json` need no token, on purpose: they
describe the API and hold no data, the source is public, and hiding the
structure would be security by obscurity. Security scans report the open
documentation as a finding; this is the reason it is accepted. Swagger UI
keeps a token in the browser's `localStorage` of this host until it expires
("Logout" in the Authorize dialog removes it).

## Known risks

- **Token cache**: a checked token is cached by its text for
  `IFDD_TOKEN_CACHE_TTL` seconds (default 300), and a cache hit does not
  check the expiry again. A token that expires meanwhile is accepted for up
  to that long.
- **Development mode behind the proxy**, see above.
- **Deprecated switches** `ifdd_be_enable_tls` and
  `ifdd_be_enable_letsencrypt` (here `{{ cookiecutter.ifdd_be_enable_tls }}` and
  `{{ cookiecutter.ifdd_be_enable_letsencrypt }}`): `y` would add router TLS
  labels that replace the proxy's TLS settings. Keep them at `n`.
- **No limit of request size or rate in the backend**: both come from the
  proxy (its DoS baseline).
