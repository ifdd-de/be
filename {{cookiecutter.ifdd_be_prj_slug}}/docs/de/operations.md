(ifdd-be-operations)=
# Betrieb

## Starten, Stoppen, Reihenfolge

```bash
docker compose -f docker-compose-production.yml up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down        # behält das Datenbank-Volume
```

Reihenfolge im Knoten: erst Traefik, dann die Dienste samt Keycloak, dann der
ganze Proxy mit oauth2-proxy (`.adm_03_up_services.sh` des Meta-Repos macht
genau das). Das Backend selbst braucht das Proxy-Netz und für die erste
Anfrage mit Token ein über den Proxy erreichbares Keycloak; zum Start braucht
es nur seine Datenbank.

Im Compose-Projekt wartet das Backend auf eine gesunde Datenbank
(`depends_on: condition: service_healthy`). Bei jedem Start ruft
`prestart.sh` `ifdd-be-create-tables` auf; ist die Datenbank nicht
erreichbar, scheitert der Start, und Docker startet den Container neu
(`restart: always`).

## Healthchecks

| Container | Prüfung | Intervall |
|---|---|---|
| `backend` | `GET http://127.0.0.1:{{ cookiecutter.ifdd_be_port }}/version` mit Python | 30 s, Startphase 40 s |
| `db` | `pg_isready -U <user> -d <database>` | 10 s |

Von außen: `{{ cookiecutter.ifdd_be_url }}/version` braucht kein Token und zeigt
die Version; `{{ cookiecutter.ifdd_be_url }}/prot_version` braucht eine Anmeldung
und ist das, was die UI auf ihrem Dashboard zeigt.

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f backend
```

Die Stufe kommt aus `LOG_LEVEL` in `.env` (hier
`{{ cookiecutter.ifdd_be_log_level.upper() }}`). Abgelehnte Tokens werden auf
INFO mit Grund protokolliert, Schreibkonflikte auf WARNING, unerwartete Fehler
mit Traceback. Das Access-Log von uvicorn ist an. Fehlt `IFDD_OIDC_ISSUER`,
steht einmal eine Warnung im Log: Dann wird der Aussteller der Tokens nicht
geprüft.

## Ressourcen

| Einstellung | Hier | Bedeutung |
|---|---|---|
| `MAX_WORKERS` / `WORKERS` | `{{ cookiecutter.ifdd_be_max_workers }}` | uvicorn-Prozesse |
| `IFDD_DB_POOL_SIZE`, `IFDD_DB_MAX_OVERFLOW` | Defaults 20, 0 | Datenbankverbindungen **je Prozess** |
| `JSONLD_CACHE_EXPIRE_AFTER` | Default 120 s | wie lange ein Prozess einen JSON-LD-Context behält |

Prozesse mal Pool-Größe muss unter `max_connections` der Datenbank bleiben
(bei PostgreSQL standardmäßig 100). Die Compose-Dateien setzen für Backend
und Datenbank keine Speichergrenze.

```{note}
Nicht gemessen: Speicher und CPU des Backends unter Last und passende Werte
für Prozesse und Pool. Die Werte oben sind Startwerte.
```

## Überwachung

Einen Metrik-Endpunkt gibt es nicht. Von außen beobachten lassen sich:
`/version` (läuft), `/prot_version` mit Token (Realm und Token-Prüfung
funktionieren), der Healthcheck-Zustand beider Container und die Fehlerquote
im Access-Log. Der vorgeschaltete Proxy antwortet mit 429, wenn ein Client
sein Ratenlimit überschreitet; das steht in den Logs des Proxys, nicht hier.

## Routineaufgaben

**Veraltete Versionen beenden.** `ifdd-be-purge` beendet jede aktuelle
Version, die seit 50 Stunden kein Schreibvorgang bestätigt hat (mit
Versionierung bleibt sie als Historie, ohne wird sie gelöscht). Quellen, die
ein Dokument weiter liefern, halten es am Leben: Ein unverändertes PUT
bestätigt es. Von selbst läuft der Befehl nicht; einplanen, wenn der Knoten
darauf angewiesen ist:

```bash
docker compose -f docker-compose-production.yml exec backend ifdd-be-purge
```

**Kontextmuster.** Neue Domänen-Contexts brauchen ein Kontextmuster im Realm
und eine Gruppe für Personen; das geschieht in Keycloak
(`keycloak_add_context_role.py` des Meta-Repos), nicht hier.

## Sicherung und Wiederherstellung

Was Daten enthält:

| Volume | Eingehängt unter | Inhalt |
|---|---|---|
| `ifdd_be_postgres_data` | `/var/lib/postgresql` | die Datenbank |
| `ifdd_be_postgres_data_backups` | `/backups` | leer; für Dumps gedacht |
| `.env` (Datei) | – | das Datenbank-Passwort und der FastAPI-Schlüssel |

```{note}
Nicht getestet: Für diesen Dienst wurde noch kein Sicherungs- oder
Wiederherstellungsverfahren durchgespielt. Die Befehle unten sind ein
Ausgangspunkt, kein geprüftes Verfahren.
```

```bash
# Dump in das Backup-Volume
docker compose -f docker-compose-production.yml exec db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /backups/nodes.dump'
# Wiederherstellen in eine leere Datenbank gleichen Namens
docker compose -f docker-compose-production.yml exec db \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean /backups/nodes.dump'
```

Oft ist keine Wiederherstellung nötig: Die Dokumente kommen aus ihren
Quellen, und erneutes Laden (etwa mit ct) stellt den aktuellen Stand wieder
her. Die Historie in der Systemzeit geht dabei verloren.

## Aktualisieren

**Template.** `cruft update` bringt Template-Änderungen; die Skip-Liste
schützt `.env`, `envs`, `certs`, `app/routers`, `app/settings.py` und
`tests`. Neue Einträge in `dotenv.dist` müssen von Hand in `.env`. Variablen
einer bestehenden Instanz ändert
`cruft update --variables-to-update '{"<variable>": "<value>"}'`.

**be-core.** Neues Wheel nach `wheels/` (altes heraus), neu bauen, neu
starten. Vorher das CHANGELOG lesen: Einträge mit **Incompatible** können eine
neue Tabelle verlangen.

**Tabellenaufbau.** Migrationen gibt es nicht. `ifdd-be-create-tables` legt
an, was fehlt, und lehnt eine `nodes`-Tabelle älteren Aufbaus mit einer
Meldung ab; dann die Tabelle (oder das Volume) löschen und die Daten neu
laden:

```bash
docker compose -f docker-compose-production.yml down -v   # löscht die Datenbank
docker compose -f docker-compose-production.yml up -d
```

**PostgreSQL.** Das Image-Tag ist `{{ cookiecutter.ifdd_be_postgres_image }}`.
Eine neue Hauptversion kann das Datenverzeichnis der alten nicht lesen; Dump
und Wiederherstellung, oder leer starten und neu laden.

```{note}
Nicht geprüft: was das Image `postgres:18` tut, wenn es Daten einer älteren
Hauptversion im Volume findet.
```

**Versionierungsschalter.** `IFDD_VERSIONING` darf sich jederzeit ändern; er
bestimmt nur, was künftige Schreibvorgänge mit den ersetzten Versionen tun.
