#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=/app/superset/superset_config.py

envsubst < /app/superset/data_okta.json.dist > /app/superset/data_okta.json
envsubst < /app/superset/data_google.json.dist > /app/superset/data_google.json

exec "$@"
