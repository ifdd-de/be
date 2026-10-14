(ifdd-be-index)=
# {{ cookiecutter.ifdd_be_prj_name }} (be)

Das Backend eines IFDD-Knotens: Es speichert die JSON-LD-Dokumente seiner
Domänen, liefert sie aus und prüft jede Anfrage gegen das Access-Token des
Realms. Dieses Kapitel beschreibt die Instanz `{{ cookiecutter.ifdd_be_prj_slug }}`,
erzeugt aus dem Template `ifdd-de/be`, aus der Sicht derer, die sie
einrichten, bauen, betreiben und absichern.

| | |
|---|---|
| Öffentliche URL | `{{ cookiecutter.ifdd_be_url }}` (Host `{{ cookiecutter.ifdd_be_host }}`, vom Proxy geroutet) |
| Interner Port | `{{ cookiecutter.ifdd_be_port }}` (uvicorn, nicht veröffentlicht) |
| Version der Instanz | `{{ cookiecutter.ifdd_be_version }}` |
| Laufzeit | Paket `ifdd-be-core` `~={{ cookiecutter.ifdd_be_core_version }}` |
| Datenbank | PostgreSQL, Image `{{ cookiecutter.ifdd_be_postgres_image }}` |
| Realm | `{{ cookiecutter.ifdd_oidc_realm }}`, Audience `{{ cookiecutter.ifdd_oidc_jwks_audience }}` |

## Was die Instanz enthält

Das Template ist nur ein Rahmen. Die Laufzeit (Datenmodell, bitemporale
Speicherung, JSON-LD-Verarbeitung, Token-Prüfung, Router, Doku-Seiten) ist
das Paket `ifdd-be-core`, das als versionierte Abhängigkeit ins Image kommt.
Die Instanz bringt Packaging, Container-Build, Compose-Dateien, die
Konfiguration (`.env`) und zwei Erweiterungspunkte mit: `app/settings.py`
für eigene Einstellungen und `app/routers/` für eigene Endpunkte.

## Architektur

```{mermaid}
flowchart LR
  Browser -->|HTTPS| Proxy[proxy: Traefik]
  UI[ui] -->|liest| Proxy
  CT[ct] -->|schreibt| Proxy
  TS[ts: Grafana] -->|liest| Proxy
  Proxy -->|"{{ cookiecutter.ifdd_be_host }}"| BE[be: uvicorn]
  BE -->|SQL| DB[(PostgreSQL)]
  BE -->|Signaturschlüssel JWKS| Proxy
  BE -->|JSON-LD-Contexts| Proxy
  Proxy --> KC[Keycloak]
  Proxy --> Schema[schema]
```

Das Backend ruft selbst zwei Dienste auf, beide unter ihren öffentlichen URLs
über den Proxy: Keycloak für die Schlüssel, mit denen die Access-Tokens
signiert sind, und den schema-Dienst für die JSON-LD-Contexts der Dokumente.
Im Proxy-Netz führen diese Hostnamen zu Traefik (Netz-Aliase der
Proxy-Instanz), und das Image vertraut dem Zertifikat des Proxys (siehe
{ref}`ifdd-be-setup`).

| Wer | ruft das Backend auf für |
|---|---|
| ui | Listen und Einzeldokumente, die Version auf ihrem Dashboard (`/prot_version`) |
| ct | Schreiben von Dokumenten (PUT) mit Client Credentials |
| ts (Grafana) | Lesen der Objekte neben ihren Zeitreihen |
| wf (Notebooks) | Lesen, z. B. Dokumente zählen |
| Menschen | Swagger UI und ReDoc (`/docs`, `/redoc`) |

Das Backend löst keine IRIs anderer Knoten auf und hängt von keinem anderen
Backend ab: Verknüpfungen über Knoten hinweg sind Sache der Clients.

## Kapitel

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

Die Werte der Variablen dieser Instanz und ihr Zusammenhang mit den anderen
Diensten stehen im Kapitel über die Dienst-Instanzen
({ref}`ifdd-instances-be`).
