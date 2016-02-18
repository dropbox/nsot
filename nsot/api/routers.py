# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter


__all__ = ('BulkRouter', 'BulkNestedRouter')


# Map of HTTP verbs to rest_framework_bulk operations.
BULK_OPERATIONS_MAP = {
    'put': 'bulk_update',
    'patch': 'partial_bulk_update',
    'delete': 'bulk_destroy',
}


class BulkRouter(SimpleRouter):
    """
    Map http methods to actions defined on the bulk mixins.

    Creating our own because the one from rest_framework_bulk is a subclass of
    DefaulRouter and we don't want that.
    """
    routes = copy.deepcopy(SimpleRouter.routes)
    routes[0].mapping.update(BULK_OPERATIONS_MAP)


class BulkNestedRouter(NestedSimpleRouter):
    """
    Bulk-enabled nested router.
    """
    def __init__(self, *args, **kwargs):
        super(BulkNestedRouter, self).__init__(*args, **kwargs)
        self.routes[0].mapping.update(BULK_OPERATIONS_MAP)
