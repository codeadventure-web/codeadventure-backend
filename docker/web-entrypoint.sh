#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres
echo "Waiting for db at $DB_HOST:$DB_PORT ..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 0.5
done
echo "DB is up."

# Run migrations automatically in dev
python manage.py migrate --noinput

# Optional: seed demo problems if none exist (idempotent)
python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE","config.settings.dev"))
django.setup()
from judge.models import Problem
from django.db import connection
try:
    if not Problem.objects.exists():
        from django.core.management import call_command
        call_command("seed_demo")
        print("Seeded demo data.")
    else:
        print("Demo data already present.")
except Exception as e:
    print("Seed skipped:", e)
PY

# Start Django dev server (for production switch to gunicorn)
exec python manage.py runserver 0.0.0.0:8000
