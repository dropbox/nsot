from ipaddress import ip_address
import json
import logging
from tornado.web import RequestHandler, urlparse, HTTPError
from tornado.escape import utf8
from werkzeug.http import parse_options_header

from .. import exc
from .. import models
from ..settings import settings


# Logging object
log = logging.getLogger(__name__)


# If raven library is available, modify the base handler to support Sentry.
try:
    from raven.contrib.tornado import SentryMixin
except ImportError:
    pass
else:
    class SentryHandler(SentryMixin, RequestHandler):
        pass
    RequestHandler = SentryHandler


class BaseHandler(RequestHandler):
    def initialize(self):
        self.session = self.application.my_settings.get("db_session")()

    def on_finish(self):
        self.session.close()

    def get_or_create_user(self, email):
        """Get a user or create a new one and return a User object."""
        user = self.session.query(models.User).filter_by(email=email).first()
        if not user:
            user = models.User(email=email).add(self.session)
            self.session.commit()

        return user

    def get_current_user(self):
        """Default global user fetch by user_auth_header."""

        # Fetch the email address from the auth_header (e.g. X-NSoT-Email)
        auth_header = settings.user_auth_header
        log.debug('  fetching auth_header: %s' % auth_header)
        email = self.request.headers.get(auth_header)

        if email is not None:
            log.debug('auth_header authenticated user: %s' % email)
            user = self.get_or_create_user(email)
            return user
        return None

    def get_client_ip(self):
        address, port = self.request.connection.context.address
        if not isinstance(address, unicode):
            address = unicode(address)
        return ip_address(address)

    def _is_permitted_network(self):
        if not settings.restrict_networks:
            return True

        ip = self.get_client_ip()
        for network in settings.restrict_networks:
            if ip in network:
                return True

        return False

    def prepare(self):
        log.debug('BaseHandler.prepare()')
        if not self._is_permitted_network():
            raise exc.Forbidden("Connected from forbidden network.")

        try:
            if not self.current_user:
                raise exc.Unauthorized("Not logged in.")
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)


class FeHandler(BaseHandler):

    def prepare(self):
        BaseHandler.prepare(self)
        # Need to access token to set Cookie.
        self.xsrf_token

    def render_template(self, template_name, **kwargs):
        template = self.application.my_settings["template_env"].get_template(
            template_name
        )
        content = template.render(kwargs)
        return content

    def render(self, template_name, **kwargs):
        context = {}
        context.update(self.get_template_namespace())
        context.update(kwargs)
        self.write(self.render_template(template_name, **context))

    def write_error(self, status_code, **kwargs):
        message = "An unknown problem has occured :("
        if "exc_info" in kwargs:
            inst = kwargs["exc_info"][1]
            if isinstance(inst, HTTPError):
                message = inst.log_message
            else:
                message = str(inst)

        # Pass context to the error template
        self.render("error.html", code=status_code, message=message)


class ApiHandler(BaseHandler):
    def initialize(self):
        BaseHandler.initialize(self)
        self._jbody = None

    @property
    def jbody(self):
        if self._jbody is None:
            if self.request.body:
                self._jbody = json.loads(self.request.body)
            else:
                self._jbody = {}
        return self._jbody

    def extract_token_credentials(self):
        """Extract email/auth_token from request"""
        authz = self.request.headers.get('Authorization')
        if authz and authz.lower().startswith('authtoken '):
            log.debug('Getting email/auth_token from Authorization header.')
            auth_type, data = authz.split()
            email, auth_token = data.split(':', 1)
        else:
            log.debug('Getting email/auth_token from arguments.')
            email = self.get_argument('email', None)
            auth_token = self.get_argument('auth_token', None)
        log.debug('     email: %s' % email)
        log.debug('auth_token: %s' % auth_token)
        return email, auth_token

    def get_current_user(self):
        """Try user_auth_header, then try auth_token header."""
        # Perform default authentication (user_auth_header)
        user = super(ApiHandler, self).get_current_user()
        if user is not None:
            log.debug('API login default method succeeded!')
            return user

        # Args used for auth_token auth...
        email, auth_token = self.extract_token_credentials()

        # Do we want these here or just to return a generice 401 "Login
        # required"?
        if email is None:
            raise exc.Unauthorized('Missing Required argument: email')
        if auth_token is None:
            raise exc.Unauthorized('Missing Required argument: auth_token')

        user = models.User.verify_auth_token(
            email, auth_token, session=self.session
        )

        # If user is bad this time, it's an invalid login
        if user is None:
            raise exc.Unauthorized('Invalid login/token expired.')

        log.debug('token_auth authenticated user: %s' % email)
        return user

    def check_xsrf_cookie(self):
        """Optionally check XSRF cookies on API calls."""
        if settings.api_xsrf_enabled:
            super(ApiHandler, self).check_xsrf_cookie()

    def get_pagination_values(self, max_limit=None):
        offset = int(self.get_argument("offset", 0))
        limit = self.get_argument("limit", None)
        if limit is None:
            return offset, limit

        limit = int(limit)
        if max_limit is not None and limit > max_limit:
            limit = max_limit

        return offset, limit

    def paginate_query(self, query, offset, limit):
        total = query.count()

        query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return query, total

    def prepare(self):
        BaseHandler.prepare(self)

        if self.request.method.lower() in ("put", "post"):
            content_type = parse_options_header(
                self.request.headers.get("Content-Type")
            )[0]
            if content_type.lower() != "application/json":
                raise exc.BadRequest("Invalid Content-Type for POST/PUT request.")

    def write_error(self, status_code, **kwargs):

        message = "An unknown problem has occured :("
        if "exc_info" in kwargs:
            inst = kwargs["exc_info"][1]
            if isinstance(inst, HTTPError):
                message = inst.log_message
            else:
                message = str(inst)

        self.write({
            "status": "error",
            "error": {
                "code": status_code,
                "message": message,
            },
        })

    def success(self, data):
        """200 OK"""
        self.write({
            "status": "ok",
            "data": data,
        })
        self.finish()

    def created(self, location=None, data=None):
        """201 CREATED"""
        self.set_status(201)
        if data is None:
            data = {}
        if location is not None:
            self.set_header(
                "Location",
                urlparse.urljoin(utf8(self.request.uri), utf8(location))
            )
        self.write({
            "status": "ok",
            "data": data,
        })
        self.finish()
