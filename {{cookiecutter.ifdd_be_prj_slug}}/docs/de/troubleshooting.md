(ifdd-be-troubleshooting)=
# Fehlersuche

Bekannte Fehlerbilder aus dem Aufbau von IFDD-Knoten. Bei 401 und 403 mit
`/whoami` beginnen, sonst mit `docker compose logs backend`.

## Tokens und Rollen

| Symptom | Ursache | Abhilfe |
|---|---|---|
| 401 `Token validation failed: Unable to verify token signature ... CERTIFICATE_VERIFY_FAILED` | das Image vertraut dem Zertifikat des Proxys nicht | `ca.crt` des Proxys nach `certs/` kopieren, Image neu bauen |
| 401 `Unable to verify token signature`, Keycloak nicht erreichbar | im Container löst der Realm-Host auf den Container selbst auf | den Host in `ifdd_proxy_internal_hosts` der Proxy-Instanz aufnehmen (Netz-Alias von Traefik) |
| 401 `Invalid payload padding` mit einem aus dem Browser kopierten Token | die Entwicklerwerkzeuge kürzen lange Header-Werte in der Anzeige | die Anfrage „als cURL“ kopieren oder das Token aus `localStorage` nehmen (`oidc.user:<authority>:<client>`) |
| 401 `Invalid token: not an access token` | ein ID-Token wurde geschickt | das Access-Token schicken |
| 401 `Invalid token audience` | das Token wurde für einen anderen Client ausgestellt | der Client braucht den Scope, der die Audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` hinzufügt |
| 403 `Insufficient permissions. Role ... required.` | dem Benutzer fehlt die Knotenrolle | den Benutzer in Keycloak in die passende Gruppe aufnehmen; mit `/whoami` prüfen |
| 403 `no context pattern of this client matches ...` | Domänen-Context ohne passendes Muster | Gruppe `ifdd_ctx_<muster>` (Personen) oder die Rolle (Service-Accounts) vergeben; mit `/whoami` prüfen |
| die UI zeigt nichts, obwohl die Anmeldung klappt, die Browser-Konsole meldet `400 Disallowed CORS origin` | die UI läuft auf einer anderen Origin als `IFDD_CORS_ORIGINS` | die Origin der UI in `.env` setzen, neu starten |

## JSON-LD-Contexts und Schreiben

| Symptom | Ursache | Abhilfe |
|---|---|---|
| 502 `... [loading remote context failed]; url: ...; cause: ...` | der schema-Dienst ist nicht erreichbar, seinem Zertifikat wird nicht vertraut, oder das Ratenlimit des Proxys antwortete mit 429 | die URL aus der Meldung im Container mit `curl` prüfen; CA wie oben; das Backend hält Contexts `JSONLD_CACHE_EXPIRE_AFTER` Sekunden |
| 422 `context ... is not below ...` | der `@context` des Dokuments liegt nicht unter `IFDD_SCHEMA_URL` | einen Context des schema-Dienstes dieses Knotens nutzen |
| 422 `context name ... is neither base, an aspect ... nor a domain name` | Tippfehler im Dateinamen des Contexts, oder ein Aspekt fehlt in `IFDD_ASPECTS` | den Namen oder die Konfiguration korrigieren |
| 422 `@id ... does not belong to the path ...` | der Pfad von `@id` weicht vom Anfragepfad ab | per PUT an den Pfad der `@id` des Dokuments schreiben |
| 409 `Concurrent write, retry` | zwei Schreibvorgänge desselben Dokuments im selben Moment | erneut senden |
| `No changes detected`, obwohl sich etwas geändert hat | die Änderung steckt nur in einem Wert von `c_cacheCreated`/`c_cacheUpdated` oder in einem Term, den der Context nicht definiert (JSON-LD verwirft undefinierte Terme) | den Term im Context definieren |

## Start und Image

| Symptom | Ursache | Abhilfe |
|---|---|---|
| Start scheitert mit `The nodes table has the layout of ...` | die Tabelle ist älter als das installierte be-core; Migrationen gibt es nicht | Tabelle (oder Volume) löschen, starten, Daten neu laden |
| das Image führt alten Code aus, obwohl die Versionsnummer neu ist | ein altes be-core-Wheel gleicher Version lag noch in `wheels/` | alte Wheels entfernen, das neue kopieren, neu bauen |
| die Datenbank meldet alle 10 s `FATAL: database "<user>" does not exist` | Healthcheck ohne `-d` (älteres Template) | `cruft update`; die aktuelle Prüfung nennt die Datenbank |
| `/docs` bleibt leer, Konsole: `Refused to execute inline script` | be-core vor dem 2026-10-13 (FastAPIs eigene Seiten) | be-core aktualisieren |
| „Authorize“ in Swagger UI scheitert, Konsole: `Refused to connect to 'https://.../token'` | der CSP des Proxys fehlt die Origin des Realms in `connect-src` | `ifdd_proxy_csp_api_docs` wie in der README von be-core setzen |
| „Authorize“: Keycloak meldet `Invalid parameter: redirect_uri` | dem Backend-Client fehlt `{{ cookiecutter.ifdd_be_url }}/docs/oauth2-redirect` | in der Admin-Konsole von Keycloak ergänzen |

Der Test `test_configured_aspect_routes_exist` scheitert mit FastAPI
0.141.1 und neuer (`'_IncludedRouter' object has no attribute 'path'`) in
Instanzen, die vor der Korrektur (2026-10-13) erzeugt wurden; die Routen selbst
funktionieren. `tests/` gehört der Instanz, also die Zeile von Hand in
`paths = set(client.app.openapi()["paths"])` ändern, wie im aktuellen
Template.
