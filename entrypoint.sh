#!/bin/sh
set -e
if [ "${SKIP_MIGRATE}" != "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput --fake-initial
  echo "Migrations done."
  if [ "${DOCKER_VERSION}" = "develop" ]; then
    echo "Running develop seeders..."
    python manage.py seed_admin_farm
    echo "Develop seeders done."
  fi
fi
echo "Starting command: $*"
exec "$@"
