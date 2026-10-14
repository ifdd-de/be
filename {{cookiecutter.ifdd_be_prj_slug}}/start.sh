#!/bin/sh
# Entrypoint of the backend image (replaces the start script of the former
# tiangolo base image). POSIX sh.
#
# 1. run prestart.sh (creates missing tables), as the old base image did;
# 2. start uvicorn directly (no gunicorn): the app factory of ifdd-be-core,
#    with WORKERS processes. PORT and WORKERS come from the environment.
set -e

PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
if [ -f "$PRE_START_PATH" ]; then
    echo "Running $PRE_START_PATH"
    . "$PRE_START_PATH"
fi

exec uvicorn --factory ifdd.be.core:create_app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-{{cookiecutter.ifdd_be_port}}}" \
    --workers "${WORKERS:-{{cookiecutter.ifdd_be_max_workers}}}"
