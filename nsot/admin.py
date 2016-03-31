from __future__ import unicode_literals

from custom_user.admin import EmailUserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from . import models


# We don't want to use the Group model for now.
admin.site.unregister(Group)


# Register our custom User model
class UserAdmin(EmailUserAdmin):
    fieldsets = (
        (None, {
            'fields': ('email', 'secret_key'),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
admin.site.register(get_user_model(), UserAdmin)


class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name',)
admin.site.register(models.Site, SiteAdmin)


class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_name', 'description', 'required',
                    'display', 'multi', 'site')
    list_filter = ('name', 'resource_name', 'required', 'multi', 'site')
admin.site.register(models.Attribute, AttributeAdmin)


class ValueAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'resource_name', 'resource_id')
    list_filter = ('name', 'value', 'resource_name')
admin.site.register(models.Value, ValueAdmin)


class ChangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'resource_name', 'resource_id',
                    'get_change_at', 'resource_name', 'site')
    list_filter = ('event', 'site')
admin.site.register(models.Change, ChangeAdmin)


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'site')
    list_filter = ('site',)

    fields = list_display
admin.site.register(models.Device, DeviceAdmin)


class NetworkAdmin(admin.ModelAdmin):
    mptt_level_indent = 10
    mptt_indent_field = 'cidr'
    list_display = ('cidr', 'network_address', 'prefix_length', 'ip_version',
                    'is_ip', 'parent', 'site')
    list_filter = ('prefix_length', 'is_ip', 'ip_version', 'site')

    def get_cidr(self):
        return '%s/%s' % (self.network_address, self.prefix_length)

    fields = ('network_address', 'broadcast_address', 'prefix_length',
              'ip_version', 'is_ip', 'site')
admin.site.register(models.Network, NetworkAdmin)


class InterfaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'parent', 'mac_address', 'type', 'speed')
    list_filter = ('type', 'speed')

    fields = list_display
admin.site.register(models.Interface, InterfaceAdmin)
