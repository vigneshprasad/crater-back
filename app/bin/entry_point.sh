#!/bin/bash

echo "$DJANGO_SETTINGS_MODULE"

set -e
python3 manage.py migrate
python3 manage.py collectstatic --noinput  --settings="$DJANGO_SETTINGS_MODULE" -v 0

ddtrace-run uvicorn --host 0.0.0.0 --port 8000 --loop asyncio --http h11 freelance.asgi:application --workers 5