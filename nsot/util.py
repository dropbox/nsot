import logging
import tornado

_TRUTHY = set([
    "true", "yes", "1", ""
])


def qp_to_bool(arg):
    return str(arg).lower() in _TRUTHY


def get_loglevel(args):
    verbose = args.verbose * 10
    quiet = args.quiet * 10
    return logging.getLogger().level - verbose + quiet

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        self.my_settings = kwargs.pop("my_settings", {})
        super(Application, self).__init__(*args, **kwargs)
