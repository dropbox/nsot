from __future__ import absolute_import, print_function

from gunicorn.app.base import Application

from nsot.services.base import Service


class NsotGunicornCommand(Application):
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
    name = 'http'

    def __init__(self, host=None, port=None, debug=False, workers=None,
                 worker_class=None):
        from django.conf import settings

        self.host = host or settings.NSOT_HOST
        self.port = port or settings.NSOT_PORT
        self.workers = workers

        options = {}
        options.setdefault('bind', '%s:%s' % (self.host, self.port))
        options.setdefault('timeout', 30)
        options.setdefault('proc_name', 'NSoT')
        options.setdefault('workers', 4)
        options.setdefault('worker_class', 'gevent')
        options.setdefault('access_logfile', '-')
        options.setdefault('errorlog', '-')
        options.setdefault('loglevel', 'info')
        options.setdefault('limit_request_line', 0)
        options['preload'] = False

        if workers:
            options['workers'] = workers

        if worker_class:
            options['worker_class'] = worker_class

        self.options = options

    def run(self):
        NsotGunicornCommand(self.options).run()
