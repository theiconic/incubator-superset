#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

######################################################################
# PY stage that simply does a pip install on our requirements
######################################################################
ARG PY_VER=3.6.9
FROM python:${PY_VER} AS superset-py

RUN mkdir /app \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libpq-dev \
            ## the libs above where added to support theiconic changes
            libldap2-dev \
            python-dev \
            libldap2-dev \
            libssl-dev \
            libsasl2-dev \
        && rm -rf /var/lib/apt/lists/*

# First, we just wanna install requirements, which will allow us to utilize the cache
# in order to only build if and only if requirements change
COPY ./requirements.txt /app/

RUN cd /app \
        && pip install --no-cache -r requirements.txt


# Copy and install TheIconic requirements files
COPY ./theiconic/requirements-ti.txt /app/
RUN pip install --no-cache -r /app/requirements-ti.txt

#####################################################################
# The 2 stages below are iconic dependencies to generate reports
#####################################################################
FROM node:10-jessie AS firefox
RUN wget -O firefoxSetup.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64" && \
    tar xjf firefoxSetup.tar.bz2 -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/local/bin/firefox && \
    rm firefoxSetup.tar.bz2

FROM node:10-jessie AS gecko
# INSTALLING GECKODRIVER
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && \
    tar -xzf geckodriver-v0.24.0-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    rm geckodriver-v0.24.0-linux64.tar.gz

######################################################################
# Node stage to deal with static asset construction
######################################################################
FROM node:10-jessie AS superset-node

# NPM ci first, as to NOT invalidate previous steps except for when package.json changes
RUN mkdir -p /app/superset/assets
COPY ./superset/assets/package* /app/superset/assets/
RUN cd /app/superset/assets \
        && npm ci

# Next, copy in the rest and let webpack do its thing
COPY ./superset/assets /app/superset/assets
# This is BY FAR the most expensive step (thanks Terser!)
RUN cd /app/superset/assets \
        && npm run build \
        && rm -rf node_modules


######################################################################
# Final lean image...
######################################################################
ARG PY_VER=3.6.9
FROM python:${PY_VER} AS lean

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_ENV=production \
    FLASK_APP="superset.app:create_app()" \
    PYTHONPATH="/app/pythonpath" \
    SUPERSET_HOME="/app/superset_home" \
    SUPERSET_PORT=8080

RUN useradd --user-group --no-create-home --no-log-init --shell /bin/bash superset \
        && mkdir -p ${SUPERSET_HOME} ${PYTHONPATH} \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libpq-dev \
            gettext \
        && rm -rf /var/lib/apt/lists/*

COPY --from=gecko /usr/local/bin/geckodriver /usr/local/bin/
COPY --from=firefox /opt/firefox /opt
RUN ln -s /opt/firefox/firefox /usr/local/bin/firefox

COPY --from=superset-py /usr/local/lib/python3.6/site-packages/ /usr/local/lib/python3.6/site-packages/
# Copying site-packages doesn't move the CLIs, so let's copy them one by one
COPY --from=superset-py /usr/local/bin/gunicorn /usr/local/bin/celery /usr/local/bin/flask /usr/bin/
COPY --from=superset-node /app/superset/assets /app/superset/assets

## Lastly, let's install superset itself
COPY superset /app/superset
COPY setup.py MANIFEST.in README.md /app/
RUN cd /app \
        && chown -R superset:superset * \
        && pip install -e .

COPY ./docker/docker-entrypoint.sh /usr/bin/

####################################################################
# Overwrite superset binaries with TheIconic versions
####################################################################

ARG TARGET_ENV=live
COPY --chown=superset ./theiconic/superset/bin/ /usr/local/bin/
RUN chmod +x -R /usr/local/bin/
RUN ln -sf /usr/local/bin/${TARGET_ENV}/* /usr/local/bin/

COPY ./theiconic/superset/ ./app/superset/
RUN ln -sf /app/superset/superset_config_${TARGET_ENV}.py /app/superset/superset_config.py
RUN cd /app && chown -R superset:superset *

WORKDIR /app
USER superset

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE ${SUPERSET_PORT}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]

######################################################################
# Dev image...
######################################################################
FROM lean AS dev

COPY ./requirements-dev.txt ./docker/requirements-extra.txt /app/

USER root
RUN cd /app \
    && pip install --no-cache -r requirements-dev.txt -r requirements-extra.txt
USER superset
