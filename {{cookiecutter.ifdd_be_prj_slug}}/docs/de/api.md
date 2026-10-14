(ifdd-be-api)=
# API

Das Backend dokumentiert seine HTTP-Schnittstelle selbst:

| URL | Inhalt |
|---|---|
| `{{ cookiecutter.ifdd_be_url }}/docs` | Swagger UI: lesen, anmelden, Endpunkte ausprobieren |
| `{{ cookiecutter.ifdd_be_url }}/redoc` | ReDoc: dasselbe Dokument zum Lesen, mit Suche |
| `{{ cookiecutter.ifdd_be_url }}/openapi.json` | das OpenAPI-3.1-Dokument |

Das Dokument erklärt die Begriffe (Contexts und ihre Arten, Zugriff über
Knotenrollen und Kontextmuster, Fachzeit und Systemzeit, die `c_*`-Metadaten)
und beschreibt jeden Endpunkt mit der nötigen Rolle, seinen Parametern,
seinen Fehlerantworten und Beispielen. Derselbe Inhalt ohne laufendes Backend
steht in {ref}`ifdd-be-core-api-http`; die Python-Schnittstelle der Laufzeit
in {ref}`ifdd-be-core-api-python`.

## Endpunkte in Swagger UI ausprobieren

1. `{{ cookiecutter.ifdd_be_url }}/docs` öffnen und **Authorize** klicken.
2. Unter `OAuth2AuthCode` erneut **Authorize** klicken: Die Anmeldeseite des
   Realms öffnet sich in einem neuen Fenster. Nach der Anmeldung schließt es
   sich selbst.
3. Einen Endpunkt öffnen, **Try it out**, **Execute**. Das Token geht bei
   jeder Anfrage mit; die Antwort zeigt, was das Backend für die eigenen
   Rollen liefert.

Ein Neuladen behält die Anmeldung, bis das Token abläuft (30 Minuten im Realm
des Templates). Ein Token von anderswo, etwa aus Client Credentials, gehört
unter `BearerToken`.

Was „Authorize“ braucht und warum die Seiten offen sind, steht in
{ref}`ifdd-be-security`; wenn es scheitert, siehe
{ref}`ifdd-be-troubleshooting`.

## Endpunkte zur Prüfung

| Endpunkt | Token | Antwort |
|---|---|---|
| `/version` | keines | `{"version": "{{ cookiecutter.ifdd_be_version }}"}` |
| `/prot_version` | jeder angemeldete Benutzer | `{"version": "{{ cookiecutter.ifdd_be_version }}_prot"}`; zeigt die UI |
| `/whoami` | jedes gültige Token | Benutzername, Client-Rollen, Kontextmuster |

```bash
TOKEN=...   # ein Access-Token
curl --cacert ca.crt -H "Authorization: Bearer $TOKEN" {{ cookiecutter.ifdd_be_url }}/whoami
```

```json
{"preferred_username": "ifdd-demo",
 "client_roles": ["ifdd_nodes_priv", "ifdd_nodes_ro", "ifdd_nodes_rw", "ifdd_public"],
 "context_patterns": ["ifdd.de"]}
```

## OpenAPI-Dokument exportieren

Für die HTTP-Referenz in einem Doku-Build das Dokument dieser Instanz (mit
ihren Aspekten und Routern) im Instanzverzeichnis exportieren:

```bash
python -c "import json; from app.main import app; json.dump(app.openapi(), open('openapi.json', 'w'))"
```

Die Datei aus Python heraus schreiben wie oben: Das Backend protokolliert
seinen Start auf die Standardausgabe; eine umgeleitete Ausgabe von `print`
würde Log-Zeilen in das JSON mischen.
