from ipaddress import ip_address
import json
from tornado.web import RequestHandler, urlparse
from tornado.escape import utf8

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
            return self.forbidden("Connected from forbidden network.")

        try:
            if not self.current_user:
                return self.unauthorized("Not logged in.")
        except exc.ValidationError as err:
            return self.badrequest(err.message)

    def badrequest(self, message):
        pass

    def unauthorized(self, message):
        pass


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

    def error_page(self, code, message):
        self.set_status(code)
        self.render("error.html", code=code, message=message)
        self.finish()

    def badrequest(self, message): self.error_page(400, message)
    def unauthorized(self, message): self.error_page(401, message)
    def forbidden(self, message): self.error_page(403, message)


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

    def prepare(self):
        rv = BaseHandler.prepare(self)
        if rv is not None:
            return rv

        if self.request.method.lower() in ("put", "post"):
            if self.request.headers.get("Content-Type").lower() != "application/json":
                return self.badrequest("Invalid Content-Type for POST/PUT request.")

    def head(self, *args, **kwargs):
        self.error_status(405, "Method not supported.")

    get     = head
    post    = head
    delete  = head
    patch   = head
    put     = head
    options = head

    def error(self, code, message):
        self.write({
            "status": "error",
            "error": {
                "code": code,
                "message": message,
            },
        })

    def success(self, data):
        self.write({
            "status": "ok",
            "data": data,
        })
        self.finish()

    def error_status(self, status, message):
        self.set_status(status)
        self.error(status, message)
        self.finish()

    def badrequest(self, message): self.error_status(400, message)
    def unauthorized(self, message): self.error_status(401, message)
    def forbidden(self, message): self.error_status(403, message)
    def notfound(self, message): self.error_status(404, message)
    def conflict(self, message): self.error_status(409, message)

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
