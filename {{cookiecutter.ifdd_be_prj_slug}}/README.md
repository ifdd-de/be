# {{cookiecutter.ifdd_be_prj_name}}

The JSON-LD backend of an IFDD node, generated from the template `ifdd-de/be`.
The runtime is the package `ifdd-be-core`; this repository holds the frame:
packaging, image, compose files, configuration (`.env`) and the extension
points `app/settings.py` and `app/routers/`.

## Quick start

```bash
cp <be-core>/dist/ifdd_be_core-*.whl wheels/   # while ifdd-be-core is not on PyPI
cp <proxy instance>/certs/ca.crt certs/         # trust the proxy's certificate
docker compose -f docker-compose-production.yml up -d --build
curl --cacert certs/ca.crt {{cookiecutter.ifdd_be_url}}/version
```

The API is documented at `{{cookiecutter.ifdd_be_url}}/docs` (Swagger UI) and
`{{cookiecutter.ifdd_be_url}}/redoc`.

## Documentation

Setup, build and release, operations, security, troubleshooting, reference
and API of this instance:

- English: [docs/en/index.md](docs/en/index.md)
- Deutsch: [docs/de/index.md](docs/de/index.md)

The pages are Sphinx sources in MyST Markdown, meant to be copied into a
documentation project that covers all services; GitHub shows them as plain
Markdown.

## AI assistance

Some parts of the template `ifdd-de/be` this instance was generated
from, in particular the tests, the test data and the documentation, were
developed or improved with the help of large language models (LLMs). All
changes were reviewed and released by the maintainer.

## License

BSD-3-Clause, see `LICENSE`.
