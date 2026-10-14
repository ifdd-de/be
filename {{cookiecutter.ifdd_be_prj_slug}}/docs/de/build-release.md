(ifdd-be-build-release)=
# Bauen und Freigeben

## Images

| Datei | Image | Zweck |
|---|---|---|
| `Dockerfile` | `{{ cookiecutter.ifdd_registry_url }}/{{ cookiecutter.ifdd_be_prj_slug }}:{{ cookiecutter.ifdd_be_version }}` | Produktion |
| `Dockerfile.dev` | gebaut von `docker-compose-development.yml` | Entwicklung mit automatischem Neuladen |

Beide beruhen auf `python:3.14-slim` und starten uvicorn direkt (ohne
gunicorn) mit der App-Fabrik von `ifdd-be-core`. Das Produktions-Image

1. installiert die Instanz und `ifdd-be-core` mit `pip install --find-links /tmp/wheels`,
   ein Wheel in `wheels/` hat also Vorrang vor dem Paketindex;
2. übernimmt jede `*.crt`- und `*.pem`-Datei aus `certs/` in den
   System-Speicher und lässt `SSL_CERT_FILE` und `REQUESTS_CA_BUNDLE` darauf
   zeigen (Token-Schlüssel und JSON-LD-Contexts werden über HTTPS geholt);
3. prüft sich selbst mit einem Healthcheck auf `/version` (Python, kein curl
   im Image).

```bash
docker compose -f docker-compose-production.yml build     # eine Instanz
./.adm_02_build_services.sh production                    # alle, aus dem Meta-Repo
```

Nach jeder Änderung an `wheels/`, `certs/` oder `app/` neu bauen: Das Image
übernimmt sie beim Bauen.

## Das be-core-Wheel

Solange `ifdd-be-core` nicht auf PyPI veröffentlicht ist, installiert das
Image es aus `wheels/`:

1. das Wheel aus dem aktuellen Quelltext von be-core bauen (dort
   `python -m build` oder `uv build`);
2. ältere Wheels gleicher Version aus `wheels/` entfernen;
3. das neue kopieren und das Image neu bauen.

Ohne Schritt 2 kann das Image einen alten Build unter derselben
Versionsnummer enthalten. `/openapi.json` nennt die be-core-Version in der
Beschreibung; zwei Builds derselben Version unterscheidet sie nicht.

## Versionen

| Wert | Hier | Quelle |
|---|---|---|
| Version der Instanz | `{{ cookiecutter.ifdd_be_version }}` | Template-Variable `ifdd_be_version`; Image-Tag, `/version`, OpenAPI-Dokument |
| be-core-Abhängigkeit | `~={{ cookiecutter.ifdd_be_core_version }}` | Template-Variable `ifdd_be_core_version`, in `pyproject.toml` |

Das Schema ist `JJ.MM.N` (26.10.1 ist die erste Version im Oktober 2026).
Beide Werte kommen aus dem Template, nicht aus `.cookiecutter_all.yaml`;
eine neue Template-Version bringt sie mit `cruft update` mit.

## CI der Instanz

`.github/workflows/ci.yml` läuft bei jedem Push und Pull Request:

- **test**: installiert die Instanz mit ihren Dev-Extras und ruft `pytest`;
- **template drift**: `cruft check` und `cruft diff`, beide nur zur
  Information (sie lassen den Lauf nicht scheitern). Was `cruft diff` zeigt,
  gehört entweder zurück ins Template oder auf die Skip-Liste.

## Freigabe

`.github/workflows/release.yml` baut das Produktions-Image und schiebt es nach
`ghcr.io/<owner>/<repository>`, sobald ein Tag `v*` gepusht wird (Tags aus
dem Tag-Namen, der Version und dem Commit). Es nutzt das `GITHUB_TOKEN` des
Laufs; weitere Secrets braucht es nicht. Der lokale Image-Name oben
(`{{ cookiecutter.ifdd_registry_url }}/...`) ist davon unabhängig.

```{note}
Nicht getestet: der Freigabe-Workflow auf GitHub und der Image-Build selbst
(die Template-Tests rendern und installieren die Instanz ohne Docker).
```
