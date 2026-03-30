#!/usr/bin/env bash
python manage.py migrate --noinput --fake-initial
uvicorn django_portal.asgi:application --host 0.0.0.0 --port ${PORT:-10000}
