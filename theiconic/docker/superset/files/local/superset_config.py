# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import json
import base64
import io

from flask_appbuilder.security.manager import AUTH_DB
from celery.schedules import crontab
from flask import Blueprint, render_template, g, redirect, request


# Import some libraries that are required
from flask_appbuilder.security.views import expose
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.security.manager import BaseSecurityManager
from flask_appbuilder.security.manager import AUTH_REMOTE_USER


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = 'The environment variable {} was missing, abort...'\
                        .format(var_name)
            raise EnvironmentError(error_msg)


ROW_LIMIT = get_env_variable("SUPERSET_ROW_LIMIT")
QUERY_SEARCH_LIMIT = get_env_variable("SUPERSET_QUERY_SEARCH_LIMIT")

APP_ICON = get_env_variable("SUPERSET_APP_ICON")
APP_THEME = "flatly.css"

SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 6
SQLLAB_TIMEOUT = 600
SUPERSET_WEBSERVER_TIMEOUT = 600
WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True

# Whether to run the web server in debug mode or not
DEBUG = get_env_variable("SUPERSET_ENV") != "production"

# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
# The authentication type
# AUTH_OID : Is for OpenID
# AUTH_DB : Is for database (username/password()
# AUTH_LDAP : Is for LDAP
# AUTH_REMOTE_USER : Is for using REMOTE_USER from web server
AUTH_TYPE = AUTH_DB

# Google Credentials
# google_creds = json.loads(base64.b64decode(os.environ.get("SUPERSET_GOOGLE_CREDENTIALS")).decode('utf-8'))
# with io.open('data.json', 'w', encoding='utf-8') as gcf:
#     gcf.write(json.dumps(google_creds, ensure_ascii=False))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data.json"


# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'mysql://{db_user}:{db_password}@{db_host}/{db_name}'.\
    format(db_user=get_env_variable("SUPERSET_DB_USER"),
           db_password=get_env_variable("SUPERSET_DB_PASSWORD"),
           db_host=get_env_variable("SUPERSET_DB_HOST"),
           db_name=get_env_variable("SUPERSET_DB_NAME")
           )

# Redis configuration
CACHE_DEFAULT_TIMEOUT = get_env_variable("SUPERSET_CACHE_REDIS_DEFAULT_TIMEOUT")
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
    'CACHE_KEY_PREFIX': 'superset_results',
    'CACHE_REDIS_URL': 'redis://{redis_host}:{redis_port}/0'
    .format(redis_host=get_env_variable("SUPERSET_CACHE_REDIS_SERVICE_HOST"),
            redis_port=get_env_variable("SUPERSET_CACHE_REDIS_SERVICE_PORT")),
}

# Set this to false if you don't want users to be able to request/grant
# datasource access requests from/to other users.
ENABLE_ACCESS_REQUEST = True

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = get_env_variable("SUPERSET_MAPBOX_API_KEY")

# CSV Options: key/value pairs that will be passed as argument to DataFrame.to_csv
# method.
# note: index option should not be overridden
CSV_EXPORT = {
    'encoding': 'utf-8',
}

# Enable / disable scheduled email reports
ENABLE_SCHEDULED_EMAIL_REPORTS = True
# If enabled, certail features are run in debug mode
# Current list:
# * Emails are sent using dry-run mode (logging only)
SCHEDULED_EMAIL_DEBUG_MODE = get_env_variable("SUPERSET_SCHEDULED_EMAIL_DEBUG_MODE", False)

# Email reports - minimum time resolution (in minutes) for the crontab
EMAIL_REPORTS_CRON_RESOLUTION = get_env_variable("SUPERSET_EMAIL_REPORTS_CRON_RESOLUTION", 15)

# Email report configuration
# From address in emails
EMAIL_REPORT_FROM_ADDRESS = get_env_variable("SUPERSET_EMAIL_REPORT_FROM_ADDRESS", "superset@theiconic.com.au")

# Send bcc of all reports to this address. Set to None to disable.
# This is useful for maintaining an audit trail of all email deliveries.
EMAIL_REPORT_BCC_ADDRESS = get_env_variable("SUPERSET_EMAIL_REPORT_BCC_ADDRESS", None)

# User credentials to use for generating reports
# This user should have permissions to browse all the dashboards and
# slices.
# TODO: In the future, login as the owner of the item to generate reports
EMAIL_REPORTS_USER = "admin"
EMAIL_REPORTS_SUBJECT_PREFIX = get_env_variable("SUPERSET_EMAIL_REPORTS_SUBJECT_PREFIX", "[Report] - ")

# The webdriver to use for generating reports. Use one of the following
# firefox
#   Requires: geckodriver and firefox installations
#   Limitations: can be buggy at times
# chrome:
#   Requires: headless chrome
#   Limitations: unable to generate screenshots of elements
EMAIL_REPORTS_WEBDRIVER = "firefox"
WEBDRIVER_BASEURL = get_env_variable("SUPERSET_WEBDRIVER_BASEURL")
# Window size - this will impact the rendering of the data
WEBDRIVER_WINDOW = {"dashboard": (1600, 2000), "slice": (3000, 1200)}

# Any config options to be passed as-is to the webdriver
WEBDRIVER_CONFIGURATION = {}
AUTH_ROLE_PUBLIC = get_env_variable("SUPERSET_AUTH_ROLE_PUBLIC")

# smtp server configuration
EMAIL_NOTIFICATIONS = True  # all the emails are sent using dryrun
SMTP_HOST = get_env_variable("SUPERSET_SMTP_HOST")
SMTP_STARTTLS = get_env_variable("SUPERSET_SMTP_STARTTLS")
SMTP_SSL = get_env_variable("SUPERSET_SMTP_SSL")
SMTP_USER = get_env_variable("SUPERSET_SMTP_USER")
SMTP_PORT = get_env_variable("SUPERSET_SMTP_PORT")
SMTP_PASSWORD = get_env_variable("SUPERSET_SMTP_PASSWORD")
SMTP_MAIL_FROM = get_env_variable("SUPERSET_SMTP_MAIL_FROM")



# # Create a custom view to authenticate the user
# AuthRemoteUserView=BaseSecurityManager.authremoteuserview
# class AirbnbAuthRemoteUserView(AuthRemoteUserView):
#     @expose('/login/')
#     def login(self):
#       print("This is LOGIN")
#       return ("This is the response from your custom authenticator")
#
#
# # Create a custom Security manager that override the authremoteuserview with the one I've created
# class CustomSecurityManager(SecurityManager):
#     authremoteuserview = AirbnbAuthRemoteUserView
#
# # Use my custom authenticator
# CUSTOM_SECURITY_MANAGER = CustomSecurityManager
#
# # User remote authentication
# AUTH_TYPE = AUTH_REMOTE_USER



# Superset has a Celery task that will periodically warm up the cache based on different strategies.
# This will cache all the charts in the top 5 most popular dashboards every hour.
# CELERYBEAT_SCHEDULE = {
#     'cache-warmup-hourly': {
#         'task': 'cache-warmup',
#         'schedule': crontab(minute=0, hour='*'),  # hourly
#         'kwargs': {
#             'strategy_name': 'top_n_dashboards',
#             'top_n': 5,
#             'since': '7 days ago',
#         },
#     },
# }


# RENDER CUSTOM WELCOME PAGE
landing_page = Blueprint('landing_page', __name__, template_folder='templates')


@landing_page.route('/superset/welcome')
def show():
    try:
        return render_template('superset/welcome.html')
    except TemplateNotFound:
        abort(404)


BLUEPRINTS = [landing_page]
