#!/bin/bash

echo "$DJANGO_SETTINGS_MODULE"

set -e
celery -A freelance worker -l info --concurrency=4 && celery -A freelance beat -l info
