#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional: auto-populate mock data and remap images on every deploy (safe/no-op if already present)
python manage.py seed_dogs --count 20 || true
python manage.py seed_accessories --count 24 || true
python manage.py remap_media || true


