from __future__ import absolute_import, print_function

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
                 worker_class=None, timeout=None, loglevel='info',
                 preload=False, max_requests=0, max_requests_jitter=0):

        options = {
            'bind': '%s:%s' % (host, port),
            'workers': workers,
            'worker_class': worker_class,
            'timeout': timeout,
            'proc_name': 'NSoT',
            'access_logfile': '-',  # 'accesslog': '-',
            'errorlog': '-',
            'loglevel': loglevel,
            'limit_request_line': 0,
            'preload_app': preload,
            'max_requests': max_requests,
            'max_requests_jitter': max_requests_jitter,
        }

        self.options = options

        print(
            'Running service: %r, num workers: %s, worker timeout: %s' % (
                self.name, self.options['workers'], self.options['timeout']
            )
        )

    def run(self):
        NsotGunicornCommand(self.options).run()
