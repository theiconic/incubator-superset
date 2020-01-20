# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Utility functions used across Superset"""

import logging
import time
import urllib.request
from collections import namedtuple
from datetime import datetime, timedelta
from email.utils import make_msgid, parseaddr
from urllib.error import URLError  # pylint: disable=ungrouped-imports

import croniter
import simplejson as json
from dateutil.tz import tzlocal
from flask import render_template, Response, session, url_for
from flask_babel import gettext as __
from flask_login import login_user
from retry.api import retry_call
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import chrome, firefox
from werkzeug.http import parse_cookie

import os
# Superset framework imports
from superset import app, db, security_manager
from superset.extensions import celery_app
from superset.models.schedules import (
    EmailDeliveryType,
    get_scheduler_model,
    ScheduleType,
    SliceEmailReportFormat,
)
from superset.utils.core import get_email_address_list, send_email_smtp
from cryptography.fernet import Fernet

# Globals
config = app.config
logging.getLogger("tasks.email_reports").setLevel(logging.INFO)

# Time in seconds, we will wait for the page to load and render
PAGE_RENDER_WAIT = 10


EmailContent = namedtuple("EmailContent", ["body", "data", "images"])


def _get_recipients(schedule):
    logging.debug("_get_recipients")
    bcc = config.get("EMAIL_REPORT_BCC_ADDRESS", None)

    if schedule.deliver_as_group:
        to = schedule.recipients
        yield (to, bcc)
    else:
        for to in get_email_address_list(schedule.recipients):
            yield (to, bcc)


def _deliver_email(schedule, subject, email):
    for (to, bcc) in _get_recipients(schedule):
        logging.debug("_deliver_email {}".format(to))
        send_email_smtp(
            to,
            subject,
            email.body,
            config,
            data=email.data,
            images=email.images,
            bcc=bcc,
            mime_subtype="related",
            dryrun=config["SCHEDULED_EMAIL_DEBUG_MODE"],
        )


def _generate_mail_content(schedule, screenshot, name, url):
    logging.debug("_generate_mail_content")
    if schedule.delivery_type == EmailDeliveryType.attachment:
        images = None
        data = {"screenshot.png": screenshot}
        body = __(
            '<b><a href="%(url)s">Explore in Superset</a></b><p></p>',
            name=name,
            url=url,
        )

        logging.debug("_generate_mail_content 1")
    elif schedule.delivery_type == EmailDeliveryType.inline:
        # Get the domain from the 'From' address ..
        # and make a message id without the < > in the ends
        domain = parseaddr(config["SMTP_MAIL_FROM"])[1].split("@")[1]
        msgid = make_msgid(domain)[1:-1]

        images = {msgid: screenshot}
        data = None
        body = __(
            """
            <b><a href="%(url)s">Explore in Superset</a></b><p></p>
            <img src="cid:%(msgid)s">
            """,
            name=name,
            url=url,
            msgid=msgid,
        )

    logging.debug("_generate_mail_content 2")
    return EmailContent(body, data, images)


def _get_auth_cookies():
    # Login with the user specified to get the reports
    with app.test_request_context():
        user = security_manager.find_user(username=os.getenv('SUPERSET_SVC_LOGIN_USER'))
        logging.debug("user {}".format(user))
        login_user(user)

        logging.debug("_get_auth_cookies 1")
        # A mock response object to get the cookie information from
        response = Response()
        app.session_interface.save_session(app, session, response)

    cookies = []

    logging.debug("_get_auth_cookies 2")
    # Set the cookies in the driver
    for name, value in response.headers:
        logging.debug("_get_auth_cookies 3")
        if name.lower() == "set-cookie":
            logging.debug("_get_auth_cookies 4")
            cookie = parse_cookie(value)
            cookies.append(cookie["session"])

    return cookies


def _get_url_path(view, **kwargs):
    with app.test_request_context():
        return urllib.parse.urljoin(
            str(config["WEBDRIVER_BASEURL"]), url_for(view, **kwargs)
        )


def create_webdriver():

    firefoxProfile = firefox.firefox_profile.FirefoxProfile()
    firefoxProfile.set_preference("general.useragent.override", "SSWORKER_FIREFOX_BROWSER")

    logging.debug("create_webdriver")
    # Create a webdriver for use in fetching reports
    if config["EMAIL_REPORTS_WEBDRIVER"] == "firefox":
        driver_class = firefox.webdriver.WebDriver
        options = firefox.options.Options()
    elif config["EMAIL_REPORTS_WEBDRIVER"] == "chrome":
        driver_class = chrome.webdriver.WebDriver
        options = chrome.options.Options()

    options.add_argument("--headless")
    logging.debug("create_webdriver 1")
    # Prepare args for the webdriver init
    kwargs = dict(options=options, firefox_profile=firefoxProfile)
    kwargs.update(config.get("WEBDRIVER_CONFIGURATION"))

    # Initialize the driver
    driver = driver_class(**kwargs)
    logging.debug("create_webdriver 2")

    #Login request with credentials
    secret_key = os.getenv('SUPERSET_SVC_LOGIN_ENCRYPTION_SECRET')
    fernet = Fernet(secret_key)
    svcuser = fernet.encrypt((os.getenv('SUPERSET_SVC_LOGIN_USER')).encode()).decode()
    svcauthkey = fernet.encrypt((os.getenv('SUPERSET_SVC_LOGIN_AUTH_KEY')).encode()).decode()
    baseurl = config.get('WEBDRIVER_BASEURL')
    # Create login url & call it
    login_url = "{baseurl}/login?svcuser={svcuser}&svcauthkey={svcauthkey}" \
        .format(baseurl=baseurl,
                svcuser=svcuser,
                svcauthkey=svcauthkey)
    driver.get(login_url)
    time.sleep(PAGE_RENDER_WAIT)

    # Set the cookies in the driver
    for cookie in _get_auth_cookies():
        logging.debug("create_webdriver 5")
        info = dict(name="session", value=cookie)
        driver.add_cookie(info)
    logging.debug("create_webdriver 6")
    return driver


def destroy_webdriver(driver):
    """
    Destroy a driver
    """

    # This is some very flaky code in selenium. Hence the retries
    # and catch-all exceptions
    try:
        retry_call(driver.close, tries=2)
    except Exception:  # pylint: disable=broad-except
        pass
    try:
        driver.quit()
    except Exception:  # pylint: disable=broad-except
        pass


def deliver_dashboard(schedule):
    """
    Given a schedule, delivery the dashboard as an email report
    """
    dashboard = schedule.dashboard
    logging.debug("deliver_dashboard")
    dashboard_url = _get_url_path("Superset.dashboard", dashboard_id=dashboard.id)

    logging.debug("deliver_dashboard {}".format(dashboard_url))
    # Create a driver, fetch the page, wait for the page to render
    driver = create_webdriver()
    window = config["WEBDRIVER_WINDOW"]["dashboard"]
    driver.set_window_size(*window)
    driver.get(dashboard_url)
    time.sleep(PAGE_RENDER_WAIT)

    logging.debug("deliver_dashboard 0 page_source {}".format(driver.page_source))
    logging.debug("deliver_dashboard 1")

    logging.debug("deliver_dashboard wait is over")

    # Set up a function to retry once for the element.
    # This is buggy in certain selenium versions with firefox driver
    get_element = getattr(driver, "find_element_by_class_name")
    element = retry_call(
        get_element, fargs=["grid-container"], tries=2, delay=PAGE_RENDER_WAIT
    )
    logging.debug("deliver_dashboard 2")
    try:
        logging.debug("deliver_dashboard 3")
        screenshot = element.screenshot_as_png
        logging.debug("deliver_dashboard 4")
    except WebDriverException:
        logging.debug("deliver_dashboard 5")
        # Some webdrivers do not support screenshots for elements.
        # In such cases, take a screenshot of the entire page.
        screenshot = driver.screenshot()  # pylint: disable=no-member
        logging.debug("deliver_dashboard 6")
    finally:
        logging.debug("deliver_dashboard 7")
        destroy_webdriver(driver)

    # Generate the email body and attachments
    email = _generate_mail_content(
        schedule, screenshot, dashboard.dashboard_title, dashboard_url
    )
    logging.debug("deliver_dashboard 8")
    subject = __(
        "%(prefix)s %(title)s",
        prefix=config["EMAIL_REPORTS_SUBJECT_PREFIX"],
        title=dashboard.dashboard_title,
    )
    logging.debug("deliver_dashboard 9")
    _deliver_email(schedule, subject, email)


def _get_slice_data(schedule):
    slc = schedule.slice

    slice_url = _get_url_path(
        "Superset.explore_json", csv="true", form_data=json.dumps({"slice_id": slc.id})
    )

    # URL to include in the email
    url = _get_url_path("Superset.slice", slice_id=slc.id)

    cookies = {}
    for cookie in _get_auth_cookies():
        cookies["session"] = cookie

    opener = urllib.request.build_opener()
    opener.addheaders.append(("Cookie", f"session={cookies['session']}"))
    response = opener.open(slice_url)
    if response.getcode() != 200:
        raise URLError(response.getcode())

    # TODO: Move to the csv module
    lines = response.fp.read()
    rows = [r.split(b",") for r in lines.splitlines()]

    if schedule.delivery_type == EmailDeliveryType.inline:
        data = None

        # Parse the csv file and generate HTML
        columns = rows.pop(0)
        with app.app_context():
            body = render_template(
                "superset/reports/slice_data.html",
                columns=columns,
                rows=rows,
                name=slc.slice_name,
                link=url,
            )

    elif schedule.delivery_type == EmailDeliveryType.attachment:
        data = {__("%(name)s.csv", name=slc.slice_name): lines}
        body = __(
            '<b><a href="%(url)s">%(name)s</a></b><p></p>',
            name=slc.slice_name,
            url=url,
        )

    return EmailContent(body, data, None)


def _get_slice_visualization(schedule):

    logging.debug("_get_slice_visualization")
    slc = schedule.slice

    # Create a driver, fetch the page, wait for the page to render
    driver = create_webdriver()
    window = config["WEBDRIVER_WINDOW"]["slice"]
    driver.set_window_size(*window)
    logging.debug("_get_slice_visualization 1")
    slice_url = _get_url_path("Superset.slice", slice_id=slc.id)

    driver.get(slice_url)
    time.sleep(PAGE_RENDER_WAIT)
    logging.debug("_get_slice_visualization 2")

    time.sleep(PAGE_RENDER_WAIT)
    logging.debug("_get_slice_visualization wait is over")


    # Set up a function to retry once for the element.
    # This is buggy in certain selenium versions with firefox driver
    element = retry_call(
        driver.find_element_by_class_name,
        fargs=["chart-container"],
        tries=2,
        delay=PAGE_RENDER_WAIT,
    )
    logging.debug("_get_slice_visualization 4")
    try:
        screenshot = element.screenshot_as_png
    except WebDriverException:
        logging.debug("_get_slice_visualization 5")
        # Some webdrivers do not support screenshots for elements.
        # In such cases, take a screenshot of the entire page.
        screenshot = driver.screenshot()  # pylint: disable=no-member
    finally:
        logging.debug("_get_slice_visualization 6")
        destroy_webdriver(driver)
    logging.debug("_get_slice_visualization 7")
    # Generate the email body and attachments
    return _generate_mail_content(schedule, screenshot, slc.slice_name, slice_url)


def deliver_slice(schedule):
    """
    Given a schedule, delivery the slice as an email report
    """
    logging.debug("deliver_slice")
    if schedule.email_format == SliceEmailReportFormat.data:
        logging.debug("deliver_slice 1")
        email = _get_slice_data(schedule)
    elif schedule.email_format == SliceEmailReportFormat.visualization:
        logging.debug("deliver_slice 2")
        email = _get_slice_visualization(schedule)
    else:
        raise RuntimeError("Unknown email report format")
    logging.debug("deliver_slice 3")
    subject = __(
        "%(prefix)s %(title)s",
        prefix=config["EMAIL_REPORTS_SUBJECT_PREFIX"],
        title=schedule.slice.slice_name,
    )
    logging.debug("deliver_slice 4")
    _deliver_email(schedule, subject, email)


@celery_app.task(
    name="email_reports.send",
    bind=True,
    soft_time_limit=config["EMAIL_ASYNC_TIME_LIMIT_SEC"],
)
def schedule_email_report(
    task, report_type, schedule_id, recipients=None
):  # pylint: disable=unused-argument
    model_cls = get_scheduler_model(report_type)
    schedule = db.create_scoped_session().query(model_cls).get(schedule_id)

    logging.debug("schedule_email_report")
    # The user may have disabled the schedule. If so, ignore this
    if not schedule or not schedule.active:
        logging.info("Ignoring deactivated schedule")
        return

    # TODO: Detach the schedule object from the db session
    if recipients is not None:
        schedule.id = schedule_id
        schedule.recipients = recipients

    logging.debug("schedule_email_report 1")
    if report_type == ScheduleType.dashboard.value:
        logging.debug("schedule_email_report 2")
        deliver_dashboard(schedule)
    elif report_type == ScheduleType.slice.value:
        logging.debug("schedule_email_report 3")
        deliver_slice(schedule)
    else:
        raise RuntimeError("Unknown report type")


def next_schedules(crontab, start_at, stop_at, resolution=0):
    crons = croniter.croniter(crontab, start_at - timedelta(seconds=1))
    previous = start_at - timedelta(days=1)

    for eta in crons.all_next(datetime):
        # Do not cross the time boundary
        if eta >= stop_at:
            break

        if eta < start_at:
            continue

        # Do not allow very frequent tasks
        if eta - previous < timedelta(seconds=resolution):
            continue

        yield eta
        previous = eta


def schedule_window(report_type, start_at, stop_at, resolution):
    """
    Find all active schedules and schedule celery tasks for
    each of them with a specific ETA (determined by parsing
    the cron schedule for the schedule)
    """
    model_cls = get_scheduler_model(report_type)
    dbsession = db.create_scoped_session()
    schedules = dbsession.query(model_cls).filter(model_cls.active.is_(True))

    for schedule in schedules:
        args = (report_type, schedule.id)

        # Schedule the job for the specified time window
        for eta in next_schedules(
            schedule.crontab, start_at, stop_at, resolution=resolution
        ):
            schedule_email_report.apply_async(args, eta=eta)


@celery_app.task(name="email_reports.schedule_hourly")
def schedule_hourly():
    """ Celery beat job meant to be invoked hourly """

    if not config["ENABLE_SCHEDULED_EMAIL_REPORTS"]:
        logging.info("Scheduled email reports not enabled in config")
        return

    resolution = config["EMAIL_REPORTS_CRON_RESOLUTION"] * 60

    # Get the top of the hour
    start_at = datetime.now(tzlocal()).replace(microsecond=0, second=0, minute=0)
    stop_at = start_at + timedelta(seconds=3600)
    schedule_window(ScheduleType.dashboard.value, start_at, stop_at, resolution)
    schedule_window(ScheduleType.slice.value, start_at, stop_at, resolution)
