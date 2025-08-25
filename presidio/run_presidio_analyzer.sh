#!/usr/bin/env bash

echo "WORKERS $WORKERS"
echo "PORT $PORT"

poetry run opentelemetry-instrument gunicorn -w $WORKERS -b 0.0.0.0:$PORT 'app:create_app()'
