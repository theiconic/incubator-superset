# This file is designed for Production & Staging environment

FROM python:3.6-jessie AS base

LABEL maintainer="Data Platforms <data_platforms@theiconic.com.au>"

ARG SUPERSET_USER="superset"

RUN cp /usr/share/zoneinfo/Australia/Sydney /etc/localtime

# Add a normal user
RUN useradd --user-group --create-home --no-log-init --shell /bin/bash ${SUPERSET_USER}

# Configure environment
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/home/superset

# Install dependencies to fix `curl https support error` and `elaying package configuration warning`
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y apt-transport-https \
        apt-utils \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        libsasl2-dev \
        libldap2-dev \
        libxi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install extra useful tool for development
RUN apt-get update -y && apt-get install --no-install-recommends -y vim less postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/*

FROM node:10-alpine AS build_assets
WORKDIR /home/superset

COPY ./superset/ ./

# BUILD ASSETS
RUN cd assets \
    && npm ci \
    && npm run build \
    && rm -rf node_modules

FROM node:10-alpine AS firefox
# INSTALLING FIREFOX
RUN wget -O firefoxSetup.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64" && \
    tar xjf firefoxSetup.tar.bz2 -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    rm firefoxSetup.tar.bz2

FROM node:10-alpine AS gecko
# INSTALLING GECKODRIVER
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && \
    tar -xzf geckodriver-v0.24.0-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    rm geckodriver-v0.24.0-linux64.tar.gz


FROM base AS install-python-packages

# EMAIL REPORTS REQUIREMENTS
RUN apt-get update -y && apt-get install --no-install-recommends -y libgtk-3-dev libdbus-glib-1-dev libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY docker/requirements-extra.txt .
COPY theiconic/docker/superset/requirements-ti.txt .

RUN pip install --cache-dir /tmp/pip --upgrade setuptools pip \
    && pip install -r requirements.txt -r requirements-extra.txt -r requirements-ti.txt \
    && rm -rf /tmp/pip


FROM install-python-packages as final

WORKDIR ${HOME}/superset

COPY --from=firefox /opt/firefox /usr/local/bin/
COPY --from=gecko /usr/local/bin/geckodriver /usr/local/bin/
COPY --from=build_assets ${HOME}/ ./

WORKDIR ${HOME}/

COPY theiconic/docker/superset/files/live/docker-entrypoint.sh /usr/local/bin/
COPY theiconic/docker/superset/files/live/docker-init.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-init.sh

ARG SUPERSET_DIR=${HOME}/superset

COPY theiconic/docker/superset/files/assets /assets

COPY theiconic/docker/superset/files/live/start_webserver.sh /usr/local/bin/
COPY theiconic/docker/superset/files/live/start_scheduler.sh /usr/local/bin/
COPY theiconic/docker/superset/files/live/start_worker.sh /usr/local/bin/
COPY theiconic/docker/superset/files/live/start_monitoring.sh /usr/local/bin/
COPY theiconic/docker/superset/files/live/superset_config.py /superset_config.py
COPY theiconic/docker/superset/files/live/superset/tasks/schedules.py /schedules.py
COPY theiconic/docker/superset/files/live/superset/utils/decorators.py /decorators.py
COPY theiconic/docker/superset/files/live/okta_security.py /okta_security.py
COPY theiconic/docker/superset/files/live/data_okta.json.dist /data_okta.json.dist
COPY theiconic/docker/superset/files/live/data_google.json.dist /data_google.json.dist

RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/start_webserver.sh
RUN chmod +x /usr/local/bin/start_scheduler.sh
RUN chmod +x /usr/local/bin/start_worker.sh
RUN chmod +x /usr/local/bin/start_monitoring.sh

RUN cp /assets/html/welcome.html ${SUPERSET_DIR}/templates/superset/welcome.html
RUN cp /assets/html/navbar.html ${SUPERSET_DIR}/templates/appbuilder/navbar.html
RUN cp /assets/html/navbar_right.html ${SUPERSET_DIR}/templates/appbuilder/navbar_right.html
RUN cp /assets/html/traceback.html ${SUPERSET_DIR}/traceback.html

RUN cp /assets/js/chartAction.js ${SUPERSET_DIR}/assets/src/chart/chartAction.js

RUN cp /assets/css/bootstrap.min.css ${SUPERSET_DIR}/static/assets/dist/bootstrap.min.css
RUN cp /assets/css/custom.css ${SUPERSET_DIR}/static/assets/dist/custom.css

RUN cp /assets/images/favicon.png ${SUPERSET_DIR}/static/assets/images/superset-logo@2x.png
RUN cp /assets/images/favicon.png ${SUPERSET_DIR}/static/assets/dist/favicon.png

# PROD & STAGE needs to be authenticate by OKTA
RUN cp /data_okta.json.dist .
RUN cp /data_google.json.dist .
RUN cp /okta_security.py superset/
RUN cp /superset_config.py ${SUPERSET_DIR}/
RUN cp /schedules.py ${SUPERSET_DIR}/tasks/
RUN cp /decorators.py ${SUPERSET_DIR}/utils/

# PROD & STAGE needs to be authenticate by OKTA
RUN cp /data_okta.json.dist .
RUN cp /data_google.json.dist .
RUN cp /okta_security.py superset/
RUN cp /superset_config.py ${SUPERSET_DIR}/
RUN cp /schedules.py ${SUPERSET_DIR}/tasks/
RUN cp /decorators.py ${SUPERSET_DIR}/utils/

ENV PATH=${SUPERSET_DIR}/bin:$PATH \
    PYTHONPATH=${HOME}:${HOME}/superset

RUN apt-get update -y && apt-get install --no-install-recommends -y gettext-base

ENTRYPOINT ["start_webserver.sh"]

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE 8088
