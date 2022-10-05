#!/bin/bash

echo "$DJANGO_SETTINGS_MODULE"

env="$ENVIRONMENT"
local_env="local"
echo "$env"

set -e
python3 manage.py migrate
python3 manage.py collectstatic --noinput  --settings="$DJANGO_SETTINGS_MODULE" -v 0

if [ "$env" == "$local_env" ]
then
  echo "Running on reload 3 workers"
  uvicorn --host 0.0.0.0 --port 8000 --loop asyncio freelance.asgi:application --workers 3 --reload
else
  echo "Running on 5 workers"
  uvicorn --host 0.0.0.0 --port 8000 --loop asyncio freelance.asgi:application --workers 5
fi
