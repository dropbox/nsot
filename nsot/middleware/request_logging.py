
"""
Middleware to log HTTP requests.
"""

from django.utils.log import getLogger
from time import time


class LoggingMiddleware(object):
    def __init__(self):
        self.logger = getLogger('nsot_server')

    def process_request(self, request):
        request.timer = time()
        return None

    def process_response(self, request, response):
        self.logger.info(
            '%s %s %s (%s) %.2fms',
            response.status_code,
            request.method,
            request.get_full_path(),
            request.META.get('REMOTE_ADDR'),
            (time() - request.timer) * 1000  # ms
        )
        return response
