#!/bin/sh
set -e
if [ "${SKIP_MIGRATE}" != "1" ]; then
  echo "Running migrations..."
  python manage.py makemigrations --noinput
  python manage.py migrate --noinput --fake-initial
  echo "Migrations done."
  if [ "${DOCKER_VERSION}" = "develop" ]; then
    echo "Running develop seeders..."
    python manage.py seed_currency
    python manage.py seed_admin_farm
    python manage.py seed_sensor_7_in_1
    python manage.py seed_province_city
    echo "Develop seeders done."
  fi
fi
echo "Starting command: $*"
exec "$@"
