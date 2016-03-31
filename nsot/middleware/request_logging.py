"""
Middleware to log HTTP requests.
"""

from time import time

from django.utils.log import getLogger


class LoggingMiddleware(object):
    def __init__(self):
        self.logger = getLogger('nsot_server')

    def process_request(self, request):
        request.timer = time()
        return None

    def process_response(self, request, response):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request_ip_path = '%s, %s' % (
                request.META.get('REMOTE_ADDR'),
                request.META.get('HTTP_X_FORWARDED_FOR')
            )
        else:
            request_ip_path = request.META.get('REMOTE_ADDR')
        self.logger.info(
            '%s %s %s (%s) %.2fms',
            response.status_code,
            request.method,
            request.get_full_path(),
            request_ip_path,
            (time() - request.timer) * 1000  # ms
        )
        return response
