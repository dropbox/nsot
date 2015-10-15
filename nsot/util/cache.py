"""
Used for caching read-only REST API responses (provided by drf-extensions).
"""

import logging
from rest_framework_extensions.key_constructor import bits, constructors
from django.core.cache import cache as djcache
from django.utils import timezone
from django.utils.encoding import force_text


log = logging.getLogger(__name__)


__all__ = ('object_key_func', 'list_key_func')


class UpdatedAtKeyBit(bits.KeyBitBase):
    """Used to store/retrieve timestamp from the cache."""
    def get_data(self, **kwargs):
        key = 'api_updated_at_timestamp'
        value = djcache.get(key, None)
        if not value:
            value = timezone.now()
            djcache.set(key, value=value)

        return force_text(value)


class ObjectKeyConstructor(constructors.DefaultKeyConstructor):
    """Cache key generator for object/detail views."""
    retrieve_sql = bits.RetrieveSqlQueryKeyBit()
    updated_at = UpdatedAtKeyBit()
    kwargs = bits.KwargsKeyBit()
    params = bits.QueryParamsKeyBit()
    unique_view_id = bits.UniqueMethodIdKeyBit()
    format = bits.FormatKeyBit()
object_key_func = ObjectKeyConstructor()


class ListKeyConstructor(constructors.DefaultKeyConstructor):
    """Cache key generator for list views."""
    list_sql = bits.ListSqlQueryKeyBit()
    pagination = bits.PaginationKeyBit()
    updated_at = UpdatedAtKeyBit()
    kwargs = bits.KwargsKeyBit()
    params = bits.QueryParamsKeyBit()
    unique_view_id = bits.UniqueMethodIdKeyBit()
    format = bits.FormatKeyBit()
list_key_func = ListKeyConstructor()
