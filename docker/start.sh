#!/bin/bash

set -e

while ! (timeout 3 bash -c "</dev/tcp/${POSTGRES_HOST}/${POSTGRES_PORT}") &> /dev/null;
do
    echo waiting for PostgreSQL to start...;
    sleep 3;
done;

./manage.py migrate  --no-input --traceback
./manage.py collectstatic --no-input --traceback
#./manage.py makemessages --locale=ru --extension=html,txt,py --ignore=venv
#./manage.py compilemessages --locale=ru
# daphne -b 0.0.0.0 -p 8000 freelance.asgi:application
./manage.py runserver 0.0.0.0:8000
# uvicorn --host 0.0.0.0 --port 8000 --loop asyncio --http h11 freelance.asgi:application --workers 3
