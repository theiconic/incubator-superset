from flask import redirect, g, flash, request
from flask_appbuilder.security.views import UserDBModelView,AuthDBView,UserLDAPModelView
from superset.security import SupersetSecurityManager
from flask_appbuilder.security.views import expose
from flask_appbuilder.security.manager import BaseSecurityManager
from flask_login import login_user, logout_user
from flask_appbuilder.security.manager import AUTH_OID
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_oidc import OpenIDConnect
from flask_appbuilder.security.views import AuthOIDView
from flask_login import login_user
from okta import UsersClient
import os
from cryptography.fernet import Fernet
import logging


class AuthOIDCView(AuthOIDView):

    @expose('/login/', methods=['GET', 'POST'])
    def login(self, flag=True):
        sm = self.appbuilder.sm
        oidc = sm.oid

        def is_service_login():

            try:
                request_user = request.args.get('svcuser', None)
                request_auth_key = request.args.get('svcauthkey', None)

                svc_encryption_secret = os.getenv('SUPERSET_SVC_LOGIN_ENCRYPTION_SECRET', None)
                svc_user = os.getenv('SUPERSET_SVC_LOGIN_USER', None)
                svc_auth_key = os.getenv('SUPERSET_SVC_LOGIN_AUTH_KEY', None)

                # Empty value check: Invalid service login if any of variable with invalid value
                if (not request_user
                        or not request_auth_key
                        or not svc_user
                        or not svc_auth_key):
                    logging.error("Superset service login: empty value found")
                    return False

                # Valid value check: Invalid service if request variables doesn't match with config variables
                fernet = Fernet(svc_encryption_secret)
                request_user = fernet.decrypt(request_user.encode()).decode()
                request_auth_key = fernet.decrypt(request_auth_key.encode()).decode()

                logging.debug("=========This is Cred=========")
                logging.debug("request_user: {}".format(request_user))
                logging.debug("request_auth_key: {}".format(request_auth_key))
                logging.debug("svc_encryption_secret: {}".format(svc_encryption_secret))
                logging.debug("svc_user: {}".format(svc_user))
                logging.debug("svc_auth_key: {}".format(svc_auth_key))

                if (request_user == svc_user
                        and request_auth_key == svc_auth_key):
                    return True
                return False
            except BaseException as ex:
                logging.error("Superset service account login failed error: {error}".format(error=str(ex)))
                return False

        def handle_service_login():

            srv_user = os.getenv('SUPERSET_SVC_LOGIN_USER', None)
            user = sm.find_user(username=srv_user)
            if user:
                login_user(user)
                logging.debug("Superset service login: valid user")

            return redirect(self.appbuilder.get_url_for_index)

        @self.appbuilder.sm.oid.require_login
        def handle_okta_login():
            okta_client = UsersClient("https://theiconic.okta.com/",
                                      os.environ["SUPERSET_OKTA_CLIENT_API"])
            user = sm.auth_user_oid(oidc.user_getfield("email"))
            if user is None:
                user = sm.add_user(okta_client.get_user(oidc.user_getfield("sub")).profile.login,
                    okta_client.get_user(oidc.user_getfield("sub")).profile.firstName,
                                   okta_client.get_user(oidc.user_getfield("sub")).profile.lastName,
                                   okta_client.get_user(oidc.user_getfield("sub")).profile.email,
                                   sm.find_role('Consumers'))

            login_user(user, remember=False)
            return redirect(self.appbuilder.get_url_for_index)

        if is_service_login():
            return handle_service_login()
        return handle_okta_login()

    @expose('/logout/', methods=['GET', 'POST'])
    def logout(self):
        oidc = self.appbuilder.sm.oid
        oidc.logout()
        super(AuthOIDCView, self).logout()
        redirect_url = request.url_root.strip('/') + self.appbuilder.get_url_for_login

        return redirect(
            oidc.client_secrets.get('issuer'))

class OIDCSecurityManager(SupersetSecurityManager):
    def __init__(self, appbuilder):
        super(OIDCSecurityManager, self).__init__(appbuilder)
        if self.auth_type == AUTH_OID:
            self.oid = OpenIDConnect(self.appbuilder.get_app)
        self.authoidview = AuthOIDCView
