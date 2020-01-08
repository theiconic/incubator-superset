# This file is designed for Production & Staging environment

FROM python:3.6-jessie

Maintainer Data Platforms <data_platforms@theiconic.com.au>

ARG SUPERSET_BRANCH="master"

USER root

RUN cp /usr/share/zoneinfo/Australia/Sydney /etc/localtime

# Add a normal user
RUN useradd --user-group --create-home --no-log-init --shell /bin/bash superset

# Configure environment
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/home/superset \
    SUPERSET_DIR=theiconic-superset

RUN apt-get update -y

# Install dependencies to fix `curl https support error` and `elaying package configuration warning`
RUN apt-get install -y apt-transport-https apt-utils

# Install superset dependencies
# https://superset.incubator.apache.org/installation.html#os-dependencies
RUN apt-get install -y build-essential libssl-dev \
    libffi-dev python3-dev libsasl2-dev libldap2-dev libxi-dev

# Install extra useful tool for development
RUN apt-get install -y vim less postgresql-client redis-tools

# Install nodejs for custom build
# https://superset.incubator.apache.org/installation.html#making-your-own-build
# https://nodejs.org/en/download/package-manager/
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs

# If commit hash on superset has changed, invalidate the docker image cache
ARG SUPERSET_LATEST_COMMIT=${SUPERSET_LATEST_COMMIT}
RUN echo "Last commit $SUPERSET_LATEST_COMMIT"

WORKDIR /home/superset

RUN echo "Start cloning $SUPERSET_BRANCH branch"
RUN git clone -b "$SUPERSET_BRANCH" https://github.com/theiconic/incubator-superset.git $SUPERSET_DIR

RUN cp $SUPERSET_DIR/requirements.txt .
RUN cp $SUPERSET_DIR/requirements-dev.txt .
RUN cp $SUPERSET_DIR/contrib/docker/requirements-extra.txt .

RUN pip install --upgrade setuptools pip \
    && pip install -r requirements.txt -r requirements-dev.txt -r requirements-extra.txt

# THE ICONIC CUSTOM DEPENDENCIES
RUN apt-get update && apt-get install -y libmysqlclient-dev libldap2-dev apt-transport-https

COPY .cicd/docker/superset/requirements-ti.txt .

RUN pip install -r requirements-ti.txt

# EMAIL REPORTS REQUIREMENTS
RUN apt-get install -y libgtk-3-dev libdbus-glib-1-dev libx11-xcb1

# INSTALLING FIREFOX
RUN wget -O firefoxSetup.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64" && \
    tar xjf firefoxSetup.tar.bz2 -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    rm firefoxSetup.tar.bz2

# INSTALLING GECKODRIVER
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && \
    tar -xzf geckodriver-v0.24.0-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    rm geckodriver-v0.24.0-linux64.tar.gz

WORKDIR $HOME/$SUPERSET_DIR

COPY .cicd/docker/superset/files/live/docker-entrypoint.sh /usr/local/bin/
COPY .cicd/docker/superset/files/live/start_webserver.sh /usr/local/bin/
COPY .cicd/docker/superset/files/live/start_scheduler.sh /usr/local/bin/
COPY .cicd/docker/superset/files/live/start_worker.sh /usr/local/bin/
COPY .cicd/docker/superset/files/live/start_monitoring.sh /usr/local/bin/

COPY .cicd/docker/superset/files/live/superset_config.py /superset_config.py
COPY .cicd/docker/superset/files/live/superset/tasks/schedules.py /schedules.py
COPY .cicd/docker/superset/files/live/superset/utils/decorators.py /decorators.py
COPY .cicd/docker/superset/files/live/okta_security.py /okta_security.py
COPY .cicd/docker/superset/files/assets /assets
COPY .cicd/docker/superset/files/live/data_okta.json.dist /data_okta.json.dist
COPY .cicd/docker/superset/files/live/data_google.json.dist /data_google.json.dist

RUN chown -R superset:superset $HOME

RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/start_webserver.sh
RUN chmod +x /usr/local/bin/start_scheduler.sh
RUN chmod +x /usr/local/bin/start_worker.sh
RUN chmod +x /usr/local/bin/start_monitoring.sh


ENV PATH=$HOME/$SUPERSET_DIR/superset/bin:$PATH \
    PYTHONPATH=$HOME/$SUPERSET_DIR/superset/:$PYTHONPATH

USER superset

# BUILD ASSETS
RUN cd superset/assets \
    && npm ci \
    && npm run build \
    && rm -rf node_modules

RUN cp /assets/html/welcome.html superset/templates/superset/welcome.html
RUN cp /assets/html/navbar.html superset/templates/appbuilder/navbar.html
RUN cp /assets/html/navbar_right.html superset/templates/appbuilder/navbar_right.html
RUN cp /assets/html/traceback.html superset/traceback.html

RUN cp /assets/js/chartAction.js superset/assets/src/chart/chartAction.js

RUN cp /assets/css/bootstrap.min.css superset/static/assets/dist/bootstrap.min.css
RUN cp /assets/css/custom.css superset/static/assets/dist/custom.css

RUN cp /assets/images/favicon.png superset/static/assets/images/superset-logo@2x.png
RUN cp /assets/images/favicon.png superset/static/assets/dist/favicon.png

# PROD & STAGE needs to be authenticate by OKTA
RUN cp /data_okta.json.dist .
RUN cp /data_google.json.dist .
RUN cp /okta_security.py superset/
RUN cp /superset_config.py superset/
RUN cp /schedules.py superset/tasks/
RUN cp /decorators.py superset/utils/

ENTRYPOINT ["docker-entrypoint.sh"]

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE 8088
