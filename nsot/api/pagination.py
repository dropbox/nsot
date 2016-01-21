from __future__ import unicode_literals

from collections import OrderedDict
from django.template import Context, loader
import logging
from rest_framework import pagination
from rest_framework.response import Response


log = logging.getLogger(__name__)


class CustomPagination(pagination.LimitOffsetPagination):
    """Custom pagination that always shows pagination controls in list view."""
    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        # This is so we can always display pagination without having to specify
        # an upper limite.
        # if self.limit is None:
        #     return None

        self.offset = self.get_offset(request)
        self.count = pagination._get_count(queryset)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        # If we have a limit, slice it
        if self.limit:
            return list(queryset[self.offset:self.offset + self.limit])
        # Otherwise only slice from the offset
        else:
            return list(queryset[self.offset:])

    def get_next_link(self):
        if not self.limit:
            return None
        return super(CustomPagination, self).get_next_link()

    def get_previous_link(self):
        if not self.limit:
            return None
        return super(CustomPagination, self).get_previous_link()

    def get_html_context(self):
        if self.limit is None:
            return {}
        return super(CustomPagination, self).get_html_context()

    def get_paginated_response(self, data, result_key=None):
        """
        Custom pagination response that excludes next/previous.

        :param data:
            Paginated data

        :param result_key:
            If set, use this as the key to label the results data.
        """
        log.debug('request URI = %s' % self.request.build_absolute_uri())
        log.debug('request path = %s' % self.request.path)
        log.debug('request path_info = %s' % self.request.path_info)

        # If path is '/api/sites/1/attributes/', this is 'attributes'
        if result_key is None:
            result_key = self.request.path.rstrip('/').split('/')[-1]
        return Response(
            OrderedDict([
                ('status', 'ok'),
                ('data', OrderedDict(
                [
                    ('total', self.count),
                    ('limit', self.limit),
                    ('offset', self.offset),
                    # ('next', self.get_next_link()),
                    # ('previous', self.get_previous_link()),
                    (result_key, data),
                    #('results', data),  # Generic 'results' key
                ]))
            ])
        )
