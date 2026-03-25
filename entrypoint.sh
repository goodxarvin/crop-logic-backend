#!/bin/sh
set -e
if [ "${SKIP_MIGRATE}" != "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput --fake-initial
  echo "Migrations done."
fi
echo "Starting command: $*"
exec "$@"
