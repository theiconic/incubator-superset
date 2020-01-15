#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=$HOME/superset/superset_config.py

# setup Google & Okta cred
envsubst < "data_okta.json.dist" > "data_okta.json"
envsubst < "data_google.json.dist" > "data_google.json"

exec "$@"
