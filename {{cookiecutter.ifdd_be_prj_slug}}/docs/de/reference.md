(ifdd-be-reference)=
# Referenz

Die Template-Variablen dieser Instanz mit Wert und Bedeutung stehen in
{ref}`ifdd-instances-be`. Diese Seite führt auf, was keine Template-Variable
ist.

## Umgebung (`.env`)

Aus `dotenv.dist` erzeugt; das Backend liest sie über pydantic-settings und
ignoriert unbekannte Namen.

| Name | Hier | Bedeutung |
|---|---|---|
| `MAX_WORKERS` | `{{ cookiecutter.ifdd_be_max_workers }}` | uvicorn-Prozesse (`WORKERS` im Container) |
| `LOG_LEVEL` | `{{ cookiecutter.ifdd_be_log_level.upper() }}` | Log-Stufe |
| `FORWARDED_ALLOW_IPS` | `*` | Adressen, deren `X-Forwarded-*`-Headern uvicorn vertraut |
| `FASTAPI_SECRET_KEY` | erzeugt | Schlüssel der Session-Middleware |
| `API_TITLE` | `{{ cookiecutter.ifdd_be_prj_name }}` | Titel des OpenAPI-Dokuments und der Doku-Seiten |
| `IFDD_BE_VERSION` | `{{ cookiecutter.ifdd_be_version }}` | Version in `/version`, `/prot_version` und im OpenAPI-Dokument |
| `IFDD_BE_PORT` | `{{ cookiecutter.ifdd_be_port }}` | interner Port; die Compose-Dateien geben ihn als `PORT` an den Container |
| `IFDD_BE_HOST` | `{{ cookiecutter.ifdd_be_host }}` | Host nur für `python -m app.main` |
| `IFDD_BE_URL` | `{{ cookiecutter.ifdd_be_url }}` | öffentliche URL; `ifdd-be-core` liest sie nicht, sie bleibt für Menschen und Skripte |
| `IFDD_BE_AUTH_ENABLED` | `{{ cookiecutter.ifdd_be_enable_auth }}` | Tokens prüfen |
| `IFDD_VERSIONING` | `{{ cookiecutter.ifdd_be_enable_versioning }}` | ersetzte Versionen als Historie behalten |
| `IFDD_BE_SSL_ENABLED` | `{{ cookiecutter.ifdd_be_enable_tls }}` | Session-Cookie nur über HTTPS (folgt dem veralteten `ifdd_be_enable_tls`) |
| `IFDD_TYPE_URL`, `IFDD_SCHEMA_URL` | `{{ cookiecutter.ifdd_type_url }}`, `{{ cookiecutter.ifdd_schema_url }}` | Vokabulare; Contexts werden nur unterhalb der schema-URL angenommen |
| `IFDD_ASPECTS` | `{{ cookiecutter.ifdd_be_aspects }}` | REST-Pfadsegment zu Aspekt |
| `IFDD_ROLE_NODES_READ`, `IFDD_ROLE_NODES_WRITE`, `IFDD_ROLE_PUBLIC` | `{{ cookiecutter.ifdd_be_role_nodes_read }}`, `{{ cookiecutter.ifdd_be_role_nodes_write }}`, `{{ cookiecutter.ifdd_be_role_public }}` | Knotenrollen |
| `IFDD_CONTEXT_ROOT` | `{{ cookiecutter.ifdd_context_root }}` | Kontextmuster des Entwicklungsbenutzers |
| `IFDD_CORS_ORIGINS` | `["{{ cookiecutter.ifdd_ui_url }}"]` | erlaubte Browser-Origins |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` | `{{ cookiecutter.ifdd_be_postgres_host }}`, `{{ cookiecutter.ifdd_be_postgres_port }}`, `{{ cookiecutter.ifdd_be_postgres_db }}`, `{{ cookiecutter.ifdd_be_postgres_user }}` | Datenbank |
| `POSTGRES_PASSWORD` | erzeugt | Datenbank-Passwort |
| `IFDD_SERVICE_DB_URL` | aus den `POSTGRES_*`-Werten | Verbindungs-URL (`postgresql+psycopg://...`) |
| `IFDD_OIDC_TOKEN_URL`, `IFDD_OIDC_AUTHORIZATION_URL`, `IFDD_OIDC_REFRESH_URL` | Endpunkte des Realms | Anmeldung von Swagger UI |
| `IFDD_OIDC_JWKS_URL` | `{{ cookiecutter.ifdd_oidc_jwks_url }}` | Signaturschlüssel |
| `IFDD_OIDC_JWKS_AUDIENCE` | `{{ cookiecutter.ifdd_oidc_jwks_audience }}` | verlangte Audience; Client der Rollen |
| `IFDD_OIDC_ISSUER` | `{{ cookiecutter.ifdd_oidc_realm }}` | verlangter Aussteller |
| `IFDD_OIDC_JWKS_ALGORITHM` | `{{ cookiecutter.ifdd_oidc_jwks_algorithm }}` | Signaturalgorithmus |

`MODULE_NAME` und `ACCESS_LOG` sind Reste des früheren Basis-Images und ohne
Wirkung.

Weitere Einstellungen von `ifdd-be-core` mit Default, in `.env` setzbar:
`JSONLD_CACHE_EXPIRE_AFTER` (120 s), `JSONLD_LOADER_TIMEOUT` (10 s),
`IFDD_TOKEN_CACHE_SIZE` (1000), `IFDD_TOKEN_CACHE_TTL` (300 s),
`IFDD_DB_POOL_SIZE` (20), `IFDD_DB_MAX_OVERFLOW` (0),
`IFDD_DB_POOL_TIMEOUT` (30 s), `IFDD_GRAPH_PREDICATES`,
`IFDD_GRAPH_MAX_DEPTH` (4), `API_SUMMARY`.

## Ports, Netze, Volumes

| Art | Name | Hinweis |
|---|---|---|
| Port | `{{ cookiecutter.ifdd_be_port }}` | uvicorn in den Netzen; nicht auf dem Host veröffentlicht |
| Netz | `{{ cookiecutter.ifdd_proxy_network }}` (extern) | Traefik erreicht das Backend; das Backend erreicht Keycloak und schema |
| Netz | `db-net` (intern im Compose-Projekt) | Backend und Datenbank |
| Volume | `ifdd_be_postgres_data` | Datenbank, unter `/var/lib/postgresql` |
| Volume | `ifdd_be_postgres_data_backups` | unter `/backups` im Datenbank-Container |

Die Datenbank ist nur in `db-net` erreichbar; kein Port ist veröffentlicht.

## Dateien

| Pfad | Zweck |
|---|---|
| `app/main.py` | Einstieg: `create_app(settings, extra_routers=instance_routers)` |
| `app/settings.py` | Einstellungen der Instanz, eine Unterklasse von `CoreSettings` (Skip-Liste) |
| `app/routers/` | Endpunkte nur dieser Instanz (Skip-Liste) |
| `certs/` | CA-Zertifikate für das Image (git-ignored, Skip-Liste) |
| `wheels/` | lokale Wheels, etwa be-core (Build-Artefakte) |
| `prestart.sh`, `start.sh`, `start-reload.sh` | Containerstart: Tabellen anlegen, dann uvicorn |
| `docker-compose-production.yml`, `docker-compose-development.yml` | Compose-Dateien |
| `dotenv.dist`, `.env` | Vorlage der Konfiguration und Konfiguration |
| `docs/en`, `docs/de` | diese Dokumentation |

## Endpunkte

Alle Endpunkte mit Parametern, Antworten und Beispielen stehen im
OpenAPI-Dokument (`{{ cookiecutter.ifdd_be_url }}/docs`) und in
{ref}`ifdd-be-core-api-http`. Kurz:

| Endpunkt | Rolle | Zweck |
|---|---|---|
| `GET`, `POST /{segment}` | lesen | Liste eines Aspekts; `POST` mit `{"ids": [...]}` |
| `GET /{segment}/{id}` | lesen (+ Muster) | ein Dokument, alle sichtbaren Contexts |
| `PUT`, `PATCH /{segment}/{id}` | schreiben (+ Muster) | für eine Fachzeit schreiben |
| `DELETE /{segment}/{id}` | schreiben (+ Muster) | die Gültigkeit beenden |
| `GET /nodes/` | lesen | Dokumente aller Aspekte |
| `GET`, `POST /types`, `/scopes` | lesen | verwendete Werte von `objType`, `objScope` |
| `POST /graph_data` | lesen | Beziehungen als Graph-Elemente |
| `GET /version` | keine | Version |
| `GET /prot_version` | angemeldet | Version, für die UI |
| `GET /whoami` | jedes Token | Rollen und Muster des Tokens |
| `/docs`, `/redoc`, `/openapi.json` | keine | Dokumentation |

Die Segmente dieser Instanz: `{{ cookiecutter.ifdd_be_aspects }}`.
