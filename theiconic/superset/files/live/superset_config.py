# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import json
import base64
import io
from superset.okta_security import OIDCSecurityManager
from flask_appbuilder.security.manager import AUTH_OID
from flask_appbuilder.security.manager import AUTH_LDAP
from celery.schedules import crontab


# Import some libraries that are required
from flask_appbuilder.security.views import expose
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.security.manager import BaseSecurityManager
from flask_appbuilder.security.manager import AUTH_REMOTE_USER

from flask import Blueprint, render_template, g, redirect, request, session

from s3cache import S3Cache


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


# Console Log Settings
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
LOG_LEVEL = get_env_variable("SUPERSET_LOG_LEVEL")

SUPERSET_ENV = get_env_variable("SUPERSET_ENV")
ROW_LIMIT = get_env_variable("SUPERSET_ROW_LIMIT")
QUERY_SEARCH_LIMIT = get_env_variable("SUPERSET_QUERY_SEARCH_LIMIT")

APP_ICON = get_env_variable("SUPERSET_APP_ICON")
APP_THEME = "flatly.css"

SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 6
SQLLAB_TIMEOUT = 600
SUPERSET_WEBSERVER_TIMEOUT = 600
WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True

# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
# The authentication type
# AUTH_OID : Is for OpenID
# AUTH_DB : Is for database (username/password()
# AUTH_LDAP : Is for LDAP
# AUTH_REMOTE_USER : Is for using REMOTE_USER from web server

AUTH_TYPE = AUTH_OID
OIDC_CLIENT_SECRETS = 'data_okta.json'
OIDC_ID_TOKEN_COOKIE_SECURE = True
OIDC_SCOPES = ["openid", "email", "profile"]
OIDC_REQUIRE_VERIFIED_EMAIL = False
OIDC_ID_TOKEN_COOKIE_NAME = "oidc_token"
CUSTOM_SECURITY_MANAGER = OIDCSecurityManager
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = 'Consumers'
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_DURATION = 60 * 60 * 24
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True

# Google creds
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data_google.json"

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'mysql://{db_user}:{db_password}@{db_host}/{db_name}'.\
    format(db_user=get_env_variable("SUPERSET_DB_USER"),
           db_password=get_env_variable("SUPERSET_DB_PASSWORD"),
           db_host=get_env_variable("SUPERSET_DB_HOST"),
           db_name=get_env_variable("SUPERSET_DB_NAME")
           )
print("Printing DB URI")
print(SQLALCHEMY_DATABASE_URI)
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
EMAIL_REPORTS_CRON_RESOLUTION = int(get_env_variable("SUPERSET_EMAIL_REPORTS_CRON_RESOLUTION", 15))

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
EMAIL_REPORTS_USER = get_env_variable("SUPERSET_EMAIL_REPORTS_USER", "admin")
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

WEBDRIVER_OKTA_USERNAME = get_env_variable("SUPERSET_WEBDRIVER_OKTA_USERNAME")
WEBDRIVER_OKTA_PASSWORD = get_env_variable("SUPERSET_WEBDRIVER_OKTA_PASSWORD")

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


# CELERY WORKER CONFIGURATION
SUPERSET_NO_OF_WORKERS = get_env_variable("SUPERSET_NO_OF_WORKERS")


class CeleryConfig(object):
    if __name__ == '__main__':
        BROKER_URL = 'amqp://{amqp_user}:{amqp_password}@{amqp_host}:{amqp_port}/{amqp_vhost}'.\
            format(amqp_user=get_env_variable("SUPERSET_AMQP_USER"),
                   amqp_password=get_env_variable("SUPERSET_AMQP_PASSWORD"),
                   amqp_host=get_env_variable("SUPERSET_AMQP_HOST"),
                   amqp_port=get_env_variable("SUPERSET_AMQP_PORT"),
                   amqp_vhost=get_env_variable("SUPERSET_AMQP_VHOST"))
    CELERY_IMPORTS = (
        'superset.sql_lab',
        'superset.tasks',
    )
    CELERY_RESULT_BACKEND = 'amqp://{amqp_user}:{amqp_password}@{amqp_host}:{amqp_port}/{amqp_vhost}'.\
            format(amqp_user=get_env_variable("SUPERSET_AMQP_USER"),
                   amqp_password=get_env_variable("SUPERSET_AMQP_PASSWORD"),
                   amqp_host=get_env_variable("SUPERSET_AMQP_HOST"),
                   amqp_port=get_env_variable("SUPERSET_AMQP_PORT"),
                   amqp_vhost=get_env_variable("SUPERSET_AMQP_VHOST"))
    CELERYD_LOG_LEVEL = 'DEBUG'
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_ACKS_LATE = True
    CELERY_ANNOTATIONS = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
        'email_reports.send': {
            'rate_limit': '1/s',
            'time_limit': 120,
            'soft_time_limit': 150,
            'ignore_result': True,
        },
    }
    CELERYBEAT_SCHEDULE = {
        'email_reports.schedule_hourly': {
            'task': 'email_reports.schedule_hourly',
            'schedule': crontab(minute=1, hour='*'),
        },
    }


CELERY_CONFIG = CeleryConfig

# Schedule Queries
FEATURE_FLAGS = {
    # Configuration for scheduling queries from SQL Lab. This information is
    # collected when the user clicks "Schedule query", and saved into the `extra`
    # field of saved queries.
    # See: https://github.com/mozilla-services/react-jsonschema-form
    'SCHEDULED_QUERIES': {
        'JSONSCHEMA': {
            'title': 'Schedule',
            'description': (
                'In order to schedule a query, you need to specify when it '
                'should start running, when it should stop running, and how '
                'often it should run. You can also optionally specify '
                'dependencies that should be met before the query is '
                'executed. Please read the documentation for best practices '
                'and more information on how to specify dependencies.'
            ),
            'type': 'object',
            'properties': {
                'output_table': {
                    'type': 'string',
                    'title': 'Output table name',
                },
                'start_date': {
                    'type': 'string',
                    'title': 'Start date',
                    # date-time is parsed using the chrono library, see
                    # https://www.npmjs.com/package/chrono-node#usage
                    'format': 'date-time',
                    'default': 'tomorrow at 9am',
                },
                'end_date': {
                    'type': 'string',
                    'title': 'End date',
                    # date-time is parsed using the chrono library, see
                    # https://www.npmjs.com/package/chrono-node#usage
                    'format': 'date-time',
                    'default': '9am in 30 days',
                },
                'schedule_interval': {
                    'type': 'string',
                    'title': 'Schedule interval',
                },
                'dependencies': {
                    'type': 'array',
                    'title': 'Dependencies',
                    'items': {
                        'type': 'string',
                    },
                },
            },
        },
        'UISCHEMA': {
            'schedule_interval': {
                'ui:placeholder': '@daily, @weekly, etc.',
            },
            'dependencies': {
                'ui:help': (
                    'Check the documentation for the correct format when '
                    'defining dependencies.'
                ),
            },
        },
        'VALIDATION': [
            # ensure that start_date <= end_date
            {
                'name': 'less_equal',
                'arguments': ['start_date', 'end_date'],
                'message': 'End date cannot be before start date',
                # this is where the error message is shown
                'container': 'end_date',
            },
        ],
        # link to the scheduler; this example links to an Airflow pipeline
        # that uses the query id and the output table as its name
        'linkback': (
            'https://airflow.example.com/admin/airflow/tree?'
            'dag_id=query_${id}_${extra_json.schedule_info.output_table}'
        ),
    },
}

# Configuration to save query result of scheduled queries
S3_CACHE_BUCKET = get_env_variable("SUPERSET_S3_CACHE_BUCKET")
S3_CACHE_KEY_PREFIX = get_env_variable("SUPERSET_S3_CACHE_KEY_PREFIX")
RESULTS_BACKEND = S3Cache(S3_CACHE_BUCKET, S3_CACHE_KEY_PREFIX)

# RENDER CUSTOM WELCOME PAGE
landing_page = Blueprint('landing_page', __name__, template_folder='templates')


@landing_page.before_request
def redirect_if_not_loggedin():
    if not g.user or not g.user.get_id() or not session.get('_fresh'):
        return redirect('/login?next=' + request.path)


@landing_page.route('/superset/welcome')
def show():
    try:
        return render_template('superset/welcome.html')
    except TemplateNotFound:
        abort(404)


BLUEPRINTS = [landing_page]

