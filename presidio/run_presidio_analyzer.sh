
# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

poetry add /dist/core_telemetry_distro-0.1.0-py3-none-any.whl
poetry add /dist/core_telemetry_instrumentation-0.1.0-py3-none-any.whl

poetry add opentelemetry-instrumentation-wsgi
poetry add opentelemetry-instrumentation-flask

echo "WORKERS $WORKERS"
echo "PORT $PORT"

poetry run opentelemetry-instrument gunicorn -w $WORKERS -b 0.0.0.0:$PORT 'app:create_app()'
