from datetime import datetime
import logging
from time import time


class LoggingMiddleware(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_request(self, request):
        request.timer = time()
        return None

    def process_response(self, request, response):
        self.logger.info(
            '%s INFO %s %s %s (%s) %.2fms',
            datetime.now(),
            response.status_code,
            request.method,
            request.get_full_path(),
            request.META.get('REMOTE_ADDR'),
            (time() - request.timer) * 1000  # ms
        )
        return response
