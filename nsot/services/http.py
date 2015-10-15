from __future__ import absolute_import, print_function

from django.conf import settings
from gunicorn.app.base import Application

from nsot.services.base import Service


class NsotGunicornCommand(Application):
    """Gunicorn WSGI service."""
    def __init__(self, options):
        self.usage = None
        self.prog = None
        self.cfg = None
        self.config_file = ""
        self.options = options
        self.callable = None
        self.project_path = None
        self.do_load_config()

    def init(self, *args):
        cfg = {}
        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                cfg[k.lower()] = v
        return cfg

    def load(self):
        import nsot.wsgi
        return nsot.wsgi.application


class NsotHTTPServer(Service):
    """HTTP service options."""
    name = 'http'

    def __init__(self, host=None, port=None, debug=False, workers=None,
                 worker_class=None, timeout=None):

        self.host = host or settings.NSOT_HOST
        self.port = port or settings.NSOT_PORT

        options = {
            'bind': '%s:%s' % (self.host, self.port),
            'workers': workers or settings.NSOT_NUM_WORKERS,
            'worker_class': worker_class or 'gevent',
            'timeout': timeout or settings.NSOT_WORKER_TIMEOUT,
            'proc_name': 'NSoT',
            'access_logfile': '-',
            'errorlog': '-',
            'loglevel': 'info',
            'limit_request_line': 0,
            'preload': False,
        }

        self.options = options

    def run(self):
        print(
            'Running service: %r, num workers: %s, worker timeout: %s' % (
                self.name, self.options['workers'], self.options['timeout']
            )
        )
        NsotGunicornCommand(self.options).run()
