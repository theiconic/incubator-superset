#!/usr/bin/env bash

export TRACE=true
source <(curl "${bamboo_cicd_api_url}/v3/")

APP_NAME="superset"

DEFAULT_DOCKERFILES_PATH="${cicd_working_directory}/theiconic/docker"
CONTEXT_PATH="${cicd_working_directory}"

export DOCKER_BUILDKIT=1 \
       BUILDKIT_PROGRESS=plain

# Build nginx-redirect image
APP_NGINX_IMAGE=$(cicd::get_docker_image "${APP_NAME}" "-nginx")
echo ${APP_NGINX_IMAGE}
echo docker build -t ${APP_NGINX_IMAGE} \
    -f "${DEFAULT_DOCKERFILES_PATH}/Dockerfile-nginx-redirect" \
    ${CONTEXT_PATH}

# Build superset image
APP_IMAGE=$(cicd::get_docker_image "${APP_NAME}")
docker build -t ${APP_IMAGE} \
    -f "${cicd_working_directory}/theiconic/docker/Dockerfile" \
    ${CONTEXT_PATH}

docker push ${APP_IMAGE}
docker push ${APP_NGINX_IMAGE}


