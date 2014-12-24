from tornado.web import RequestHandler, urlparse
from tornado.escape import utf8

from .. import models
from ..settings import settings


class ApiHandler(RequestHandler):
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

    def prepare(self):
        if not self.current_user or not self.current_user.enabled:
            self.error_status(403, "Not logged in.")
            return

    def error(self, errors):
        errors = [
            {"code": code, "message": message} for code, message in errors
        ]

        self.write({
            "status": "error",
            "errors": errors,
        })

    def success(self, data):
        self.write({
            "status": "ok",
            "data": data,
        })

    def error_status(self, status, message):
        self.set_status(status)
        self.error([(status, message)])
        self.finish()

    def badrequest(self, message):
        self.error_status(400, message)

    def notfound(self, message):
        self.error_status(404, message)

    def conflict(self, message):
        self.error_status(409, message)

    def created(self, location):
        self.set_status(201)
        self.set_header(
            "Location",
            urlparse.urljoin(utf8(self.request.uri), utf8(location))
        )
        self.finish()
