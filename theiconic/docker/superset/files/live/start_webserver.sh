#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=$HOME/$SUPERSET_DIR/superset/superset_config.py

# setup Google & Okta cred
envsubst < "data_okta.json.dist" > "data_okta.json"
envsubst < "data_google.json.dist" > "data_google.json"

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
        superset:app