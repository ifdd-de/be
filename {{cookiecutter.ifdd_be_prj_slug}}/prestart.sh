# Run by the base image (tiangolo/uvicorn-gunicorn) before the server starts.
# The base image's start script sources this file with sh and `set -e`: keep
# it POSIX sh, do not change shell options, and do not exit on success.
#
# Creates the table of the backend if it does not exist yet; existing tables
# are left as they are (SQLAlchemy create_all, no migrations). If the database
# cannot be reached the start fails and the container is restarted, instead
# of serving requests without a table.
echo "prestart: creating missing tables"
ifdd-be-create-tables
