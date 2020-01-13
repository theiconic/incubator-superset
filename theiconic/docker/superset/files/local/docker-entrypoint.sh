#!/usr/bin/env bash

set -ex

export SUPERSET_CONFIG_PATH=$HOME/$SUPERSET_DIR/superset/superset_config.py

# If environment is local then setup default user

echo "RUNNING SUPERSET DB UPGRDADE"
superset db upgrade

echo "INITIALISING SUPERSET"
superset init

set -ex

if [ "$#" -ne 0 ]; then
    exec "$@"
elif [ "development" = "development" ]; then
    celery worker --app=superset.sql_lab:celery_app --pool=gevent -Ofair &
    # needed by superset runserver
    FLASK_ENV=development FLASK_APP=superset:app flask run -p 8088 --with-threads --reload --debugger --host=0.0.0.0
else
    superset --help
fi
