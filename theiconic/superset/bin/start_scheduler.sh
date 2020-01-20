#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=$HOME/$SUPERSET_DIR/superset/superset_config.py

# setup Google & Okta cred
envsubst < "data_okta.json.dist" > "data_okta.json"
envsubst < "data_google.json.dist" > "data_google.json"

celery beat \
      --app=superset.tasks.celery_app:app \
      --broker=amqp://$SUPERSET_AMQP_USER:$SUPERSET_AMQP_PASSWORD@$SUPERSET_AMQP_HOST:$SUPERSET_AMQP_PORT/$SUPERSET_AMQP_VHOST \
      --loglevel DEBUG