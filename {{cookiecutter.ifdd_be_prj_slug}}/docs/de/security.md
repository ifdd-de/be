(ifdd-be-security)=
# Sicherheit

## Anmeldung

Mit `IFDD_BE_AUTH_ENABLED=true` braucht jeder Endpunkt außer `/version` und
den Doku-Seiten ein OIDC-Access-Token des Realms
`{{ cookiecutter.ifdd_oidc_realm }}` (`Authorization: Bearer <token>`). Das
Backend prüft

- die Signatur gegen die Schlüssel des Realms (`IFDD_OIDC_JWKS_URL`, über den
  Proxy geholt),
- den Ablauf,
- die Audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` (`IFDD_OIDC_JWKS_AUDIENCE`),
- den Aussteller `IFDD_OIDC_ISSUER` (aus `ifdd_oidc_realm`; ist er leer,
  wird er nicht geprüft, und einmal steht eine Warnung im Log),
- den Token-Typ: nur Access-Tokens (`typ` = `Bearer`), nie ID-Tokens
  desselben Clients (RFC 9068).

Scheitert eine Prüfung, antwortet es 401 mit dem Grund.

Browser (die UI, Swagger UI) melden sich mit dem Authorization-Code-Flow und
PKCE an; Skripte und Dienste (ct, ts, Notebooks) nutzen Client Credentials
eigener vertraulicher Clients. Das Backend nimmt beides an, solange das
Access-Token die Rollen trägt.

## Berechtigung

Rollen sind Client-Rollen von `{{ cookiecutter.ifdd_oidc_jwks_audience }}`
(`resource_access.{{ cookiecutter.ifdd_oidc_jwks_audience }}.roles`); Personen
bekommen sie über Gruppen in Keycloak.

| Rolle | Hier | Erlaubt |
|---|---|---|
| angemeldet | `{{ cookiecutter.ifdd_be_role_public }}` | `/prot_version` |
| lesen | `{{ cookiecutter.ifdd_be_role_nodes_read }}` | jeden lesenden Endpunkt |
| schreiben | `{{ cookiecutter.ifdd_be_role_nodes_write }}` | PUT, PATCH, DELETE |

Base- und Aspekt-Contexts brauchen nur diese Rollen. Ein **Domänen-Context**
(ein Name mit Punkten wie `breaker.grid.example.ifdd.de`) braucht zusätzlich
ein **Kontextmuster**: eine Client-Rolle mit Punkt, die auf den Context-Namen
oder einen Namen darüber passt, an Label-Grenzen. `{{ cookiecutter.ifdd_context_root }}`
passt auf jeden Domänen-Context. Ohne Muster sieht ein Client keinen
Domänen-Context. Fremde Contexts geben **403, nicht 404**: Ihre Existenz
wird nicht verborgen. `/whoami` zeigt die Rollen und Muster, die das Backend
aus einem Token liest.

## Entwicklungsmodus

Mit `IFDD_BE_AUTH_ENABLED=false` wird nichts geprüft: Jede Anfrage handelt
als Entwicklungsbenutzer mit allen Knotenrollen und dem Muster
`{{ cookiecutter.ifdd_context_root }}`. `docker-compose-development.yml` schaltet
die Anmeldung ab **und** stellt das Backend unter `{{ cookiecutter.ifdd_be_host }}`
hinter Traefik: Wer den Proxy erreicht, kann alles lesen und schreiben. Den
Entwicklungsaufbau nur auf einem Rechner betreiben, den sonst niemand
erreicht.

## Secrets

| Secret | Wo | Wofür |
|---|---|---|
| `POSTGRES_PASSWORD` | `.env` (erzeugt, Rechte 0600) | der Datenbankbenutzer `{{ cookiecutter.ifdd_be_postgres_user }}` |
| `FASTAPI_SECRET_KEY` | `.env` (erzeugt) | Signatur des Session-Cookies der Session-Middleware |

Keines davon ist eine Template-Variable, keines landet in `.cruft.json`. Die
Datenbank behält das Passwort, mit dem sie angelegt wurde: Es nur in `.env`
zu ändern, sperrt das Backend aus.

## TLS und Zertifikate

Das Backend spricht in den Docker-Netzen reines HTTP auf Port
`{{ cookiecutter.ifdd_be_port }}`; TLS endet bei Traefik. Für eigene Aufrufe an
Keycloak und den schema-Dienst nutzt es HTTPS und vertraut dem
System-Speicher des Images samt den CAs aus `certs/` (siehe
{ref}`ifdd-be-build-release`). Router-Labels tragen keine `tls`-Einträge:
Ein Router mit eigener TLS-Sektion würde die TLS-Konfiguration des
Entrypoints des Proxys ersetzen.

## Container-Benutzer

Das Backend läuft im Produktions- und im Entwicklungs-Image als
unprivilegierter Benutzer `be` (UID und GID 10001), nicht als root. Der Code
gehört root und ist für `be` nur lesbar. Zur Laufzeit schreibt das Backend
keine Dateien (seine Caches liegen im Speicher) und braucht daher kein
beschreibbares Verzeichnis und kein Volume. Ein Port unter 1024 für
`ifdd_be_port` ist diesem Benutzer je nach Docker-Version womöglich nicht
erlaubt; der Default `{{ cookiecutter.ifdd_be_port }}` ist nicht betroffen. In der
Entwicklung muss das eingehängte `app/` auf dem Host für andere lesbar sein.

## Schutz im Browser

- **CORS**: `IFDD_CORS_ORIGINS` erlaubt genau die Origin der UI
  `{{ cookiecutter.ifdd_ui_url }}`. Der Preflight jeder anderen Origin wird
  abgelehnt (`400 Disallowed CORS origin`), der Browser schickt die Anfrage
  mit Token dann nie. Für die lokale UI-Entwicklung deren Origin in `.env`
  ergänzen.
- **Security-Header**: Der Proxy hängt `security-headers` an (nosniff,
  Frame-Options, Referrer-Policy, kein `Server`-Header) und die CSP
  `csp-api-docs`.
- **CSP der Doku-Seiten**: Skripte und Styles nur von diesem Host; die
  Origin des Realms in `connect-src` für „Authorize“; `blob:`-Worker und
  Inline-Styles für ReDoc. Die genaue Policy steht in der README von
  `ifdd-be-core`.

## Offene API-Dokumentation

`/docs`, `/redoc` und `/openapi.json` brauchen bewusst kein Token: Sie
beschreiben die API und enthalten keine Daten, der Quelltext ist öffentlich,
und die Struktur zu verbergen wäre Security by Obscurity. Sicherheitsscans
melden die offene Dokumentation als Befund; dies ist die Begründung, ihn zu
akzeptieren. Swagger UI hält ein Token im `localStorage` des Browsers für
diesen Host, bis es abläuft („Logout“ im Authorize-Dialog entfernt es).

## Bekannte Risiken

- **Token-Cache**: Ein geprüftes Token bleibt `IFDD_TOKEN_CACHE_TTL` Sekunden
  (Default 300) nach seinem Text im Cache, und ein Treffer prüft den Ablauf
  nicht erneut. Ein Token, das inzwischen abläuft, wird bis zu so lange
  weiter angenommen.
- **Entwicklungsmodus hinter dem Proxy**, siehe oben.
- **Veraltete Schalter** `ifdd_be_enable_tls` und
  `ifdd_be_enable_letsencrypt` (hier `{{ cookiecutter.ifdd_be_enable_tls }}` und
  `{{ cookiecutter.ifdd_be_enable_letsencrypt }}`): `y` würde Router-TLS-Labels
  setzen, die die TLS-Einstellungen des Proxys ersetzen. Auf `n` lassen.
- **Keine Begrenzung von Anfragegröße oder -rate im Backend**: Beides kommt
  vom Proxy (seine DoS-Grundsicherung).
