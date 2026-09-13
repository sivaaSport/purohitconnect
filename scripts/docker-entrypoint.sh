#!/bin/sh
set -eu

echo "[entrypoint] Waiting for database..."
python <<'PY'
import os, time, sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.docker"))
django.setup()
from django.db import connection
from django.db.utils import OperationalError

for attempt in range(1, 31):
    try:
        connection.ensure_connection()
        print(f"[entrypoint] Database ready (attempt {attempt})")
        break
    except OperationalError as exc:
        print(f"[entrypoint] DB not ready ({attempt}/30): {exc}")
        time.sleep(2)
else:
    print("[entrypoint] Database never became ready", file=sys.stderr)
    sys.exit(1)
PY

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput

if [ "${SEED_ON_START:-0}" = "1" ]; then
  echo "[entrypoint] Seeding cities/languages and sample purohits..."
  python manage.py seed_db || true
fi

echo "[entrypoint] Starting: $*"
exec "$@"
