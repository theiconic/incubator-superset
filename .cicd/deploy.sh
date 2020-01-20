#!/usr/bin/env bash

export TRACE=true
source <(curl "${bamboo_cicd_api_url}/v3/")

export APP_NAME="superset"
export APP_IMAGE=$(cicd::get_docker_image ${APP_NAME})
export APP_IMAGE_NGINX=$(cicd::get_docker_image "${APP_NAME}" "-nginx")
export SERVICE_URL="$(cicd::get_local_service_endpoint ${APP_NAME})"

cicd::secrets_export "${APP_NAME}"

# Prepare the database
export DB_INSTANCE_SIZE="db.m4.large"
export DB_STORAGE_SIZE=50
export SUPERSET_ENV="staging"
export REDIS_INSTANCE_SIZE="cache.m3.medium"

if [[ "${CICD_NAMESPACE}" == 'live' ]]; then
    SUPERSET_ENV="production"
    DB_INSTANCE_SIZE="db.m4.large"
    DB_STORAGE_SIZE=400
    REDIS_INSTANCE_SIZE="cache.m3.large"
fi

export SUPERSET_DB_HOST="${APP_NAME}-${CICD_NAMESPACE}.mysql.${SERVICE_HOST}"

# Prepare the scaling values
export APPLICATION_MIN_REPLICAS=6
[[ ${CICD_NAMESPACE} == 'live' ]] && APPLICATION_MIN_REPLICAS="6" || APPLICATION_MIN_REPLICAS="1"

export APPLICATION_MAX_REPLICAS
[[ ${CICD_NAMESPACE} == 'live' ]] && APPLICATION_MAX_REPLICAS="10" || APPLICATION_MAX_REPLICAS="1"

# Get the New Relic App ID
#NEWRELIC_API_URL="${bamboo_cicd_api_url}/v3/newrelic/application?environment=${NODE_ENV}&name=${SERVICE_URL}"
#NEWRELIC_APP_ID=$(cicd::curl_http_api "${NEWRELIC_API_URL}" | jq -r '.id')

# Remove monitoring file if NEWRELIC_APP_ID is null
#$[ "${NEWRELIC_APP_ID}" == null ] && rm ${cicd_working_directory}/.cicd/terraform/monitoring.tf.dist || true

# Set up AMQP
cicd::rabbitmq_ensure_user "${SUPERSET_CLOUDAMQP_TOKEN}" "${APP_NAME}" "${CICD_NAMESPACE}"

# Execute the application deployment
cicd::envsubst_directory "${cicd_working_directory}/.cicd/terraform"

cicd::terraform_apply \
    -auto-approve \
    -var db_endpoint="${SUPERSET_DB_HOST}" \
	-var db_name="${SUPERSET_DB_NAME}" \
	-var db_password="${SUPERSET_DB_PASSWORD}" \
	-var db_username="${SUPERSET_DB_USER}" \
	-var db_storage_size="${DB_STORAGE_SIZE}" \
	-var project="${APP_NAME}" \
	-var stack="${CICD_NAMESPACE}"

# Get db host & redis host
export SUPERSET_DB_HOST=$(cicd::terraform_get_output db_instance_address)
export SUPERSET_REDIS_HOST=$(cicd::terraform_get_output redis_instance_address)

# Execute the application deployment
cicd::envsubst_directory "${cicd_working_directory}/.cicd/k8s"

cicd::kubectl_apply

#cicd::newrelic_notify_deployment ${SERVICE_URL}
