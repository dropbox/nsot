from ipaddress import ip_address
import json
from tornado.web import RequestHandler, urlparse, HTTPError
from tornado.escape import utf8
from werkzeug.http import parse_options_header

from .. import exc
from .. import models
from ..settings import settings


class BaseHandler(RequestHandler):
    def initialize(self):
        self.session = self.application.my_settings.get("db_session")()

    def on_finish(self):
        self.session.close()

    def get_current_user(self):
        email = self.request.headers.get(settings.user_auth_header)
        if not email:
            return

        user = self.session.query(models.User).filter_by(email=email).first()
        if not user:
            user = models.User(email=email).add(self.session)
            self.session.commit()

        return user

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
        if not self._is_permitted_network():
            raise exc.Forbidden("Connected from forbidden network.")

        try:
            if not self.current_user:
                raise exc.Unauthorized("Not logged in.")
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)


class FeHandler(BaseHandler):
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

        self.render("error.html", code=status_code, message=message)



class ApiHandler(BaseHandler):
    def initialize(self):
        BaseHandler.initialize(self)
        self._jbody = None
        # Need to access token to set Cookie.
        self.xsrf_token

    @property
    def jbody(self):
        if self._jbody is None:
            if self.request.body:
                self._jbody = json.loads(self.request.body)
            else:
                self._jbody = {}
        return self._jbody

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
        self.write({
            "status": "ok",
            "data": data,
        })
        self.finish()

    def created(self, location, data):
        self.set_status(201)
        self.set_header(
            "Location",
            urlparse.urljoin(utf8(self.request.uri), utf8(location))
        )
        self.write({
            "status": "ok",
            "data": data,
        })
        self.finish()
