#!/usr/bin/env bash

set -ex

# setup Google & Okta cred
envsubst < /app/superset/data_okta.json.dist > /app/superset/data_okta.json
envsubst < /app/superset/data_google.json.dist > /app/superset/data_google.json

# If environment is local then setup default user
echo "RUNNING SUPERSET DB UPGRDADE ON PROD"
superset db upgrade

echo "INITIALISING SUPERSET"
superset init

exec gunicorn --bind  0.0.0.0:8088 \
        --worker-class gevent \
        --log-level $SUPERSET_GUNICORN_LOG_LEVEL \
        --workers $SUPERSET_NO_OF_WORKERS \
        --timeout $SUPERSET_GUNICORN_TIMEOUT \
        --limit-request-line 0 \
        --limit-request-field_size 0 \
        superset
