#!/usr/bin/env bash
uvicorn django_portal.asgi:application --host 0.0.0.0 --port ${PORT:-10000}
