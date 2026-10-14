# Backend image. Plain python:3.14-slim (Debian/glibc); the former
# tiangolo/uvicorn-gunicorn base image is no longer used. uvicorn is started
# directly (no gunicorn), see start.sh.
FROM python:3.14-slim

ENV PIP_ROOT_USER_ACTION=ignore \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1

# Local wheels, e.g. a build of ifdd-be-core that is not published yet.
# The directory is normally empty, in which case pip falls back to the index.
COPY wheels /tmp/wheels
COPY pyproject.toml /app/pyproject.toml
COPY ./app /app/app
COPY prestart.sh /app/prestart.sh
COPY start.sh /app/start.sh

WORKDIR /app
RUN pip install --no-cache-dir --find-links /tmp/wheels . \
    && rm -rf /tmp/wheels

# Additional CA certificates from certs/ (*.crt, *.pem), e.g. the CA of the
# proxy, so that the backend can reach Keycloak and the JSON-LD contexts under
# their public https URLs. Without files there the trust store stays as it is.
COPY certs/ /tmp/ifdd-certs/
RUN set -eu; \
    mkdir -p /usr/local/share/ca-certificates; \
    for f in /tmp/ifdd-certs/*.crt /tmp/ifdd-certs/*.pem; do \
        [ -f "$f" ] || continue; \
        name=$(basename "$f"); \
        cp "$f" "/usr/local/share/ca-certificates/ifdd-${name%.*}.crt"; \
    done; \
    rm -rf /tmp/ifdd-certs; \
    update-ca-certificates

# Python's ssl module (token validation: JWKS) and requests (JSON-LD contexts),
# which otherwise trusts only its own certifi bundle, use the system bundle.
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Run as the unprivileged user "be" (uid/gid 10001), not as root. The code
# stays owned by root and is only readable for it. The backend writes no files
# at run time (the JSON-LD, token and namespace caches are in memory), so it
# needs no writable directory. Read and execute rights are set here, so that
# restrictive rights in the build context (e.g. umask 077) do not matter.
RUN groupadd --system --gid 10001 be \
    && useradd --system --uid 10001 --gid be --no-create-home \
       --home-dir /nonexistent --shell /usr/sbin/nologin be \
    && chmod -R a+rX /app \
    && chmod a+rx /app/start.sh /app/prestart.sh
USER be

# Liveness probe without curl (not in this image): Python is always present.
# PORT is set by the compose file.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os,sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '{{cookiecutter.ifdd_be_port}}') + '/version', timeout=5).status == 200 else 1)"

CMD ["/app/start.sh"]
