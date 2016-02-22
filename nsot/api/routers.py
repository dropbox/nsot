# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework_bulk.routes import BulkRouter
from rest_framework_nested.routers import NestedSimpleRouter


__all__ = ('BulkRouter', 'BulkNestedRouter')


# Map of HTTP verbs to rest_framework_bulk operations.
BULK_OPERATIONS_MAP = {
    'put': 'bulk_update',
    'patch': 'partial_bulk_update',
    'delete': 'bulk_destroy',
}


class BulkNestedRouter(NestedSimpleRouter):
    """
    Bulk-enabled nested router.
    """
    def __init__(self, *args, **kwargs):
        super(BulkNestedRouter, self).__init__(*args, **kwargs)
        self.routes[0].mapping.update(BULK_OPERATIONS_MAP)
