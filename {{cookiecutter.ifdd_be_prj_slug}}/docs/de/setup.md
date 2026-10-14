(ifdd-be-setup)=
# Einrichtung

## Voraussetzungen

| Was | Warum |
|---|---|
| Docker mit Compose | Backend und Datenbank laufen als zwei Container |
| das externe Netz `proxy-net` und eine laufende Proxy-Instanz | Traefik routet `{{ cookiecutter.ifdd_be_host }}` zum Backend; das Backend erreicht Keycloak und den schema-Dienst darüber |
| der Proxy führt `{{ cookiecutter.ifdd_be_host }}`, den Keycloak-Host und den schema-Host in `ifdd_proxy_internal_hosts` | in den Containern müssen diese Namen zu Traefik führen, nicht zum Container selbst |
| eine Keycloak-Instanz mit dem Realm `{{ cookiecutter.ifdd_oidc_realm }}` | Aussteller und Signaturschlüssel der Access-Tokens |
| eine schema-Instanz unter `{{ cookiecutter.ifdd_schema_url }}` | die JSON-LD-Contexts jedes geschriebenen Dokuments |
| das be-core-Wheel in `wheels/`, solange `ifdd-be-core` nicht auf PyPI liegt | das Image installiert es von dort |
| das CA-Zertifikat des Proxys (dort `certs/ca.crt`) in `certs/` | das Image muss dem Zertifikat des Proxys vertrauen |

## Aufrufe über den Proxy prüfen

Das Backend holt die Signaturschlüssel des Realms und die JSON-LD-Contexts
unter ihren öffentlichen URLs. Aus dem laufenden Container:

```bash
docker compose -f docker-compose-production.yml exec backend python -c \
  "import os, urllib.request; print(urllib.request.urlopen(os.environ['IFDD_OIDC_JWKS_URL'], timeout=5).status)"
```

`200` heißt: Namensauflösung und Zertifikat stimmen. Sonst siehe
{ref}`ifdd-be-troubleshooting`.

## Instanz erzeugen

Meist erzeugt das Meta-Repo alle Instanzen in einem Zug
(`.adm_meta_01_all.sh`, Schritt `.adm_01_create_services.sh`): Es ruft
`cruft create` mit der gemeinsamen Variablendatei `.cookiecutter_all.yaml`
auf, kopiert das be-core-Wheel nach `wheels/` und die CA des Proxys nach
`certs/`.

Von Hand, im Verzeichnis, das die Instanzen enthält:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip envs --skip .env \
  https://github.com/ifdd-de/be
cp <be-core>/dist/ifdd_be_core-*.whl {{ cookiecutter.ifdd_be_prj_slug }}/wheels/
cp proxy/certs/ca.crt {{ cookiecutter.ifdd_be_prj_slug }}/certs/
```

Das Wheel aus dem aktuellen Quelltext von be-core bauen und ältere Wheels
gleicher Version vorher entfernen: pip nimmt jedes Wheel mit passender
Version, und ein Image mit einem alten Build unter derselben Versionsnummer
ist schon mehrfach vorgekommen (siehe {ref}`ifdd-be-troubleshooting`).

## Konfiguration und Secrets

Der Post-Hook schreibt `.env` aus `dotenv.dist` (Rechte 0600) und erzeugt
darin zwei Secrets: `FASTAPI_SECRET_KEY` und `POSTGRES_PASSWORD`. `.env`
wird nie eingecheckt und von einem späteren `cruft update` nie
überschrieben; neue Einträge in `dotenv.dist` müssen in eine bestehende
`.env` von Hand nachgetragen werden.

Alle anderen Werte kommen aus den Variablen des Templates. Sie stehen mit
Wert und Bedeutung in {ref}`ifdd-instances-be`; die, die das Verhalten des
Backends bestimmen:

| Variable | Wert hier | Wirkung |
|---|---|---|
| `ifdd_be_enable_auth` | `{{ cookiecutter.ifdd_be_enable_auth }}` | `y`: jede Anfrage braucht ein Access-Token; `n`: Entwicklungsmodus ganz ohne Prüfung |
| `ifdd_be_aspects` | `{{ cookiecutter.ifdd_be_aspects }}` | REST-Pfadsegmente und ihre Aspekte (`IFDD_ASPECTS`) |
| `ifdd_be_enable_versioning` | `{{ cookiecutter.ifdd_be_enable_versioning }}` | ersetzte Versionen als Historie behalten (`y`) oder löschen (`n`) |
| `ifdd_context_root` | `{{ cookiecutter.ifdd_context_root }}` | Kontextmuster des Entwicklungsbenutzers |
| `ifdd_ui_url` | `{{ cookiecutter.ifdd_ui_url }}` | die einzige Browser-Origin, die CORS erlaubt |

Ein Aspekt ist Konfiguration, kein Code: in `.env` zu `IFDD_ASPECTS`
hinzufügen, etwa `'{"products": "product", "assets": "asset"}'`, und neu
starten. Die einfachen Anführungszeichen um das JSON (und um `API_TITLE`)
halten `.env` für eine Shell ladbar (`set -a; . ./.env; set +a`); docker
compose und das Backend lesen den Wert ohne sie. Instanzen, die vor dieser
Änderung erzeugt wurden, haben die Werte ohne Anführungszeichen: von Hand
ergänzen, wenn `.env` in einer Shell geladen wird. Ein einfaches
Anführungszeichen innerhalb dieser Werte ist nicht möglich.

## Skip-Liste

Pfade, die zur Instanz gehören und die `cruft update` nicht anfassen darf:
`.env`, `envs`, `certs`, `app/routers`, `app/settings.py`, `tests`. Die
`pyproject.toml` des Templates führt sie unter `[tool.cruft]`; `.env` und
`envs` beim Erzeugen mit `--skip` übergeben, wie das Meta-Repo es tut.

## Erster Start

Produktion (Image aus `Dockerfile`):

```bash
docker compose -f docker-compose-production.yml build
docker compose -f docker-compose-production.yml up -d
curl --cacert ../proxy/certs/ca.crt {{ cookiecutter.ifdd_be_url }}/version
```

Das Backend wartet auf eine gesunde Datenbank, dann legt `prestart.sh` die
Extensions und die Tabelle an (`ifdd-be-create-tables`), und uvicorn
startet.

Entwicklung (`Dockerfile.dev`, `start-reload.sh`): `app/` ist in den
Container eingehängt, uvicorn lädt bei Änderungen neu; die Anmeldung ist
**aus** (`IFDD_BE_AUTH_ENABLED=false` in `docker-compose-development.yml`),
und das Image übernimmt die Zertifikate aus `certs/` nicht.

```bash
docker compose -f docker-compose-development.yml up --build
```

Ohne Docker, für die Arbeit an `app/`:

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```
