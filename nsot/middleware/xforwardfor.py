
"""
Some small middleware to allow using the X-Forward-For header
The use of this middleware is configurable in settings.py

adapted from http://www.djangobook.com/en/2.0/chapter17.html
"""
from django.conf import settings

class SetRemoteAddrFromForwardedFor(object):
    def process_request(self, request):
        try:
            if settings.NSOT_XFORWARDFOR == True:
                real_ip = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError, NameError: # if NSOT_XFORWARDFOR not set then we just
                                    # use REMOTE_ADDR anyway
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # Take just the first one.
            real_ip = real_ip.split(",")[0]
            request.META['REMOTE_ADDR'] = real_ip