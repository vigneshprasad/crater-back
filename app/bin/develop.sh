#!/bin/bash

DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-freelance.settings}
echo $DJANGO_SETTINGS_MODULE

set -e
python3 manage.py migrate
python3 manage.py collectstatic --noinput  --settings=$DJANGO_SETTINGS_MODULE -v 0
python manage.py runserver 0.0.0.0:8000 & celery -A freelance worker -l info --concurrency=4 -B && celery -A freelance beat -l info
