(ifdd-be-operations)=
# Operations

## Start, stop, order

```bash
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down        # keeps the database volume
```

Start order across the node: Traefik first, then the services including
Keycloak, then the full proxy with oauth2-proxy (`.adm_03_up_services.sh`
of the meta repository does exactly that). The backend itself needs the
proxy network and, for the first request with a token, a reachable Keycloak
behind the proxy; at start it only needs its database.

Inside the compose project the backend waits for a healthy database
(`depends_on: condition: service_healthy`). On every start `prestart.sh`
runs `ifdd-be-create-tables`; if the database cannot be reached, the start
fails and Docker restarts the container (`restart: always`).

## Health checks

| Container | Check | Interval |
|---|---|---|
| `backend` | `GET http://127.0.0.1:{{ cookiecutter.ifdd_be_port }}/version` with Python | 30 s, start period 40 s |
| `db` | `pg_isready -U <user> -d <database>` | 10 s |

From outside: `{{ cookiecutter.ifdd_be_url }}/version` needs no token and shows
the version; `{{ cookiecutter.ifdd_be_url }}/prot_version` needs a sign-in
and is what the UI shows on its dashboard.

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f backend
```

The level comes from `LOG_LEVEL` in `.env` (here
`{{ cookiecutter.ifdd_be_log_level.upper() }}`). Rejected tokens are logged at
INFO with their reason, write conflicts at WARNING, unexpected errors with
their traceback. The access log of uvicorn is on. A missing
`IFDD_OIDC_ISSUER` is logged once as a warning: then the issuer of tokens is
not checked.

## Resources

| Setting | Here | Meaning |
|---|---|---|
| `MAX_WORKERS` / `WORKERS` | `{{ cookiecutter.ifdd_be_max_workers }}` | uvicorn processes |
| `IFDD_DB_POOL_SIZE`, `IFDD_DB_MAX_OVERFLOW` | defaults 20, 0 | database connections **per process** |
| `JSONLD_CACHE_EXPIRE_AFTER` | default 120 s | how long a process keeps a JSON-LD context |

Workers times pool size must stay below the `max_connections` of the
database (100 by default in PostgreSQL). The compose files set no memory
limit for the backend or the database.

```{note}
Not measured: memory and CPU of the backend under load, and suitable values
for workers and pool. The values above are starting points.
```

## Monitoring

There is no metrics endpoint. What can be watched from outside: `/version`
(up), `/prot_version` with a token (the realm and the token check work), the
health state of both containers, and the error rate in the access log. The
proxy in front answers 429 when a client exceeds its rate limit; that shows
up in the proxy's logs, not here.

## Routine tasks

**Ending stale versions.** `ifdd-be-purge` ends every current version that
no write has confirmed for 50 hours (with versioning they stay as history,
without they are deleted). Sources that keep sending a document keep it
alive: an unchanged PUT confirms it. Nothing runs the command by itself;
schedule it if the node relies on it:

```bash
docker compose -f docker-compose-production.yml exec backend ifdd-be-purge
```

**Context patterns.** New domain contexts need a context pattern in the
realm and a group for people; that is done in Keycloak
(`keycloak_add_context_role.py` of the meta repository), not here.

## Backup and restore

What holds data:

| Volume | Mounted at | Content |
|---|---|---|
| `ifdd_be_postgres_data` | `/var/lib/postgresql` | the database |
| `ifdd_be_postgres_data_backups` | `/backups` | empty; meant for dumps |
| `.env` (file) | – | the database password and the FastAPI secret key |

```{note}
Not tested: no backup or restore procedure has been run for this service.
The commands below are a starting point, not a verified procedure.
```

```bash
# dump into the backup volume
docker compose -f docker-compose-production.yml exec db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /backups/nodes.dump'
# restore into an empty database of the same name
docker compose -f docker-compose-production.yml exec db \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean /backups/nodes.dump'
```

Often a restore is not needed: the documents come from their sources, and
loading them again (for example with ct) rebuilds the current state. The
history in system time is then lost.

## Updates

**Template.** `cruft update` brings template changes; the skip list protects
`.env`, `envs`, `certs`, `app/routers`, `app/settings.py` and `tests`. New
entries of `dotenv.dist` must be added to `.env` by hand. Variables of an
existing instance change with
`cruft update --variables-to-update '{"<variable>": "<value>"}'`.

**be-core.** New wheel into `wheels/` (old one out), rebuild, restart. Read
its CHANGELOG first: entries marked **Incompatible** may need a new table.

**Database layout.** There are no migrations. `ifdd-be-create-tables`
creates what is missing and refuses a `nodes` table of an older layout with
a message; then drop the table (or the volume) and load the data again:

```bash
docker compose -f docker-compose-production.yml down -v   # deletes the database
docker compose -f docker-compose-production.yml up -d
```

**PostgreSQL.** The image tag is `{{ cookiecutter.ifdd_be_postgres_image }}`.
A new major version cannot read the data directory of the old one; dump and
restore, or start empty and load again.

```{note}
Not checked: what the `postgres:18` image does when it finds data of an
older major version in the volume.
```

**Versioning switch.** `IFDD_VERSIONING` can change at any time; it decides
only what future writes do with the versions they replace.
