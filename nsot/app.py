
import tornado
import logging
from .routes import HANDLERS

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        kwargs["handlers"] = HANDLERS
        self.my_settings = kwargs.pop("my_settings", {})
        super(Application, self).__init__(*args, **kwargs)
