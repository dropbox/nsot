
import tornado
import logging
import mimetypes

from .routes import HANDLERS

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):

        mimetypes.add_type("application/font-woff2", ".woff2")

        kwargs["handlers"] = HANDLERS
        self.my_settings = kwargs.pop("my_settings", {})
        super(Application, self).__init__(*args, **kwargs)
