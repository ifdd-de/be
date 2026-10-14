(ifdd-be-troubleshooting)=
# Troubleshooting

Known failure patterns, from setups of IFDD nodes. Start with `/whoami` for
401 and 403, and with `docker compose logs backend` for everything else.

## Tokens and roles

| Symptom | Cause | Remedy |
|---|---|---|
| 401 `Token validation failed: Unable to verify token signature ... CERTIFICATE_VERIFY_FAILED` | the image does not trust the proxy's certificate | copy `ca.crt` of the proxy into `certs/`, rebuild the image |
| 401 `Unable to verify token signature`, Keycloak not reachable | inside the container the realm host resolves to the container itself | add the host to `ifdd_proxy_internal_hosts` of the proxy instance (network alias of Traefik) |
| 401 `Invalid payload padding` with a token copied from the browser | the browser's developer tools shorten long header values in the display | copy the request "as cURL", or take the token from `localStorage` (`oidc.user:<authority>:<client>`) |
| 401 `Invalid token: not an access token` | an ID token was sent | send the access token |
| 401 `Invalid token audience` | the token was issued for another client | the client needs the scope that adds the audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` |
| 403 `Insufficient permissions. Role ... required.` | the user lacks the node role | add the user to the matching group in Keycloak; check with `/whoami` |
| 403 `no context pattern of this client matches ...` | domain context without a matching pattern | add the group `ifdd_ctx_<pattern>` (people) or the role (service accounts); check with `/whoami` |
| UI shows nothing although the login works, browser console shows `400 Disallowed CORS origin` | the UI runs on another origin than `IFDD_CORS_ORIGINS` | set the UI origin in `.env`, restart |

## JSON-LD contexts and writes

| Symptom | Cause | Remedy |
|---|---|---|
| 502 `... [loading remote context failed]; url: ...; cause: ...` | the schema service is not reachable, its certificate is not trusted, or the proxy's rate limit answered 429 | check the URL from the detail with `curl` inside the container; CA as above; the backend caches contexts for `JSONLD_CACHE_EXPIRE_AFTER` seconds |
| 422 `context ... is not below ...` | the document's `@context` is not below `IFDD_SCHEMA_URL` | use a context of this node's schema service |
| 422 `context name ... is neither base, an aspect ... nor a domain name` | typo in the context file name, or an aspect missing in `IFDD_ASPECTS` | fix the name or the configuration |
| 422 `@id ... does not belong to the path ...` | the path of `@id` differs from the request path | PUT to the path of the document's `@id` |
| 409 `Concurrent write, retry` | two writes of the same document at the same moment | send it again |
| `No changes detected` although something changed | the change is only in a `c_cacheCreated`/`c_cacheUpdated` value or in a term the context does not define (JSON-LD drops undefined terms) | define the term in the context |

## Start and image

| Symptom | Cause | Remedy |
|---|---|---|
| start fails with `The nodes table has the layout of ...` | the table is older than the installed be-core; there are no migrations | drop the table (or the volume), start, load the data again |
| the image runs old code although the version number is new | an old be-core wheel with the same version was still in `wheels/` | remove old wheels, copy the new one, rebuild |
| the database logs `FATAL: database "<user>" does not exist` every 10 s | a health check without `-d` (older template) | `cruft update`; the current check names the database |
| `/docs` stays empty, console: `Refused to execute inline script` | be-core before 2026-10-13 (FastAPI's own pages) | update be-core |
| "Authorize" in Swagger UI fails, console: `Refused to connect to 'https://.../token'` | the CSP of the proxy lacks the realm origin in `connect-src` | set `ifdd_proxy_csp_api_docs` as in the README of be-core |
| "Authorize": Keycloak answers `Invalid parameter: redirect_uri` | the backend client lacks `{{ cookiecutter.ifdd_be_url }}/docs/oauth2-redirect` | add it in the admin console of Keycloak |

The test `test_configured_aspect_routes_exist` fails with FastAPI 0.141.1
and later (`'_IncludedRouter' object has no attribute 'path'`) in instances
generated before this was fixed (2026-10-13); the routes themselves work. `tests/` belongs to
the instance, so change the line by hand to
`paths = set(client.app.openapi()["paths"])`, as in the current template.
