#!/usr/bin/env bash

set -ex

# Create an admin user (you will be prompted to set username, first and last name before setting a password)
export FLASK_APP=superset:app
flask fab create-admin