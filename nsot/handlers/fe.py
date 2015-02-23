from .util import FeHandler

import tornado.web


class AppHandler(FeHandler):
    @tornado.web.authenticated
    def get(self):
        return self.render("app.html")
