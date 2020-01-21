#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=/app/superset/superset_config.py

# setup Google & Okta cred
envsubst < /app/superset/data_okta.json.dist > /app/superset/data_okta.json
envsubst < /app/superset/data_google.json.dist > /app/superset/data_google.json

celery beat \
      --app=superset.tasks.celery_app:app \
      --broker=amqp://$SUPERSET_AMQP_USER:$SUPERSET_AMQP_PASSWORD@$SUPERSET_AMQP_HOST:$SUPERSET_AMQP_PORT/$SUPERSET_AMQP_VHOST \
      --loglevel DEBUG