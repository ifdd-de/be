#!/bin/sh
# Development entrypoint: prestart, then uvicorn with auto-reload and a single
# worker (reload is incompatible with multiple workers). POSIX sh.
set -e

PRE_START_PATH=${PRE_START_PATH:-/app/prestart.sh}
if [ -f "$PRE_START_PATH" ]; then
    echo "Running $PRE_START_PATH"
    . "$PRE_START_PATH"
fi

exec uvicorn --factory ifdd.be.core:create_app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-{{cookiecutter.ifdd_be_port}}}" \
    --reload --reload-dir /app/app
