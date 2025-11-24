#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres
echo "Waiting for db at $DB_HOST:$DB_PORT..."
until nc -z "$DB_HOST" "$DB_PORT"; do
	sleep 0.5
done
echo "DB is up."

# Run migrations
python manage.py migrate --noinput

# Seed data (optional, only if needed)
python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE"))
django.setup()
from judge.models import Problem
try:
    if not Problem.objects.exists():
        from django.core.management import call_command
        # ensure you have a management command named 'seed_demo' or remove this block
        # call_command("seed_demo") 
        print("Seeded demo data check complete.")
except Exception as e:
    print(f"Seed skipped: {e}")
PY

# Start Server
exec python manage.py runserver 0.0.0.0:8000
