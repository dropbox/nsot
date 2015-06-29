from __future__ import unicode_literals

import ast
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from collections import OrderedDict
import json
import logging
from rest_framework import fields, serializers

from . import auth
from .. import exc
from .. import models


log = logging.getLogger(__name__)


class NsotSerializer(serializers.ModelSerializer):
    """Base serializer that logs change events."""
    def to_internal_value(self, data):
        """Inject site_pk from view's kwargs if it's not already in data."""
        view = self.context['view']
        kwargs = view.kwargs

        log.debug('NsotSerializer.to_internal_value() data [before] = %r', data)

        if 'site_id' not in data and 'site_pk' in kwargs:
            data['site_id'] = kwargs['site_pk']

        log.debug('NsotSerializer.to_internal_value() data [after] = %r', data)

        return super(NsotSerializer, self).to_internal_value(data)


######
# User
######
class UserSerializer(serializers.ModelSerializer):
    """
    UserProxy model serializer that takes optional `with_secret_key` argument
    that controls whether the secret_key for the user should be displayed.
    """
    def __init__(self, *args, **kwargs):
        # Don't pass `with_secret_key` up to the superclass
        with_secret_key = kwargs.pop('with_secret_key', None)
        super(UserSerializer, self).__init__(*args, **kwargs)

        # If we haven't passed `with_secret_key`, don't show the secret_key
        # field.
        if with_secret_key is None:
            self.fields.pop('secret_key')

    permissions = fields.ReadOnlyField(source='get_permissions')

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'permissions', 'secret_key')

######
# Site
######
class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Site

    def to_representation(self, obj):
        return obj.to_dict()


#########
# Changes
#########
class ChangeSerializer(NsotSerializer):
    """Used for displaying Change events."""
    class Meta:
        model = models.Change

    def to_representation(self, obj):
        return obj.to_dict()


###########
# Attribute
###########
class AttributeSerializer(NsotSerializer):
    """Used for GET, DELETE on Attributes."""
    class Meta:
        model = models.Attribute

    def to_representation(self, obj):
        return obj.to_dict()


class JSONDictField(fields.Field):
    """Field used to represention attributes as JSON <-> Dict."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        log.debug('JSONDictField.to_internal_value() data = %r', data)
        if not data:
            data = {}

        if isinstance(data, dict):
            return data

        # Try it as a regular JSON dict
        try:
            return json.loads(data)
        except ValueError:
            # Or try it as a Python dict
            try:
                return ast.literal_eval(data)
            except (SyntaxError, ValueError) as err:
                raise exc.ValidationError(err)
        except Exception as err:
            raise exc.ValidationError(err)
        return data


class AttributeCreateSerializer(AttributeSerializer):
    """Used for POST on Attributes."""
    constraints = JSONDictField(required=False)
    description = fields.CharField(allow_blank=True, required=False)
    site_id = fields.IntegerField()

    class Meta:
        model = models.Attribute
        fields = ('name', 'description', 'resource_name', 'required', 'display',
                  'multi', 'constraints', 'site_id')


class AttributeUpdateSerializer(AttributeCreateSerializer):
    """Used for PUT, PATCH, on Attributes."""
    class Meta:
        model = models.Attribute
        fields = ('description', 'required', 'display', 'multi', 'constraints')


#######
# Value
#######
class ValueSerializer(serializers.ModelSerializer):
    """Used for GET, DELETE on Values."""
    class Meta:
        model = models.Value
        fields = ('id', 'name', 'value', 'attribute', 'resource_name',
                  'resource')

    # Not sure if we want to view an attribute value w/ so much context just
    # yet.
    # def to_representation(self, obj):
    #      return obj.to_dict()


class ValueCreateSerializer(ValueSerializer):
    """Used for POST on Values."""
    class Meta:
        model = models.Value
        read_only_fields = ('id', 'name', 'resource_name')
        fields = ('id', 'name', 'value', 'attribute', 'resource_name',
                  'resource')


########
# Device
########
class DeviceSerializer(NsotSerializer):
    """Used for GET, DELETE on Devices."""
    class Meta:
        model = models.Device

    def to_representation(self, obj):
        if isinstance(obj, OrderedDict):
            return obj
        return obj.to_dict()


class DeviceCreateSerializer(DeviceSerializer):
    """Used for POST on Devices."""
    attributes = JSONDictField(required=False)
    site_id = fields.IntegerField()

    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes', 'site_id')

    def create(self, validated_data):
        attributes = validated_data.pop('attributes', {})
        obj = super(DeviceCreateSerializer, self).create(validated_data)
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        obj.save()
        return obj


class DeviceUpdateSerializer(DeviceCreateSerializer):
    """Used for PUT, PATCH, on Devices."""
    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes')

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes', {})
        obj = super(DeviceUpdateSerializer, self).update(
            instance, validated_data
        )
        obj.set_attributes(attributes)
        obj.save()
        return obj


#########
# Network
#########
class NetworkSerializer(NsotSerializer):
    """Used for GET, DELETE on Networks."""
    class Meta:
        model = models.Network

    def to_representation(self, obj):
        return obj.to_dict()


class NetworkCreateSerializer(NetworkSerializer):
    """Used for POST on Networks."""
    attributes = JSONDictField(required=False)
    cidr = fields.CharField(write_only=True)
    site_id = fields.IntegerField()

    class Meta:
        model = models.Network
        fields = ('cidr', 'attributes', 'site_id')

    def create(self, validated_data):
        attributes = validated_data.pop('attributes', {})
        obj = super(NetworkCreateSerializer, self).create(validated_data)
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        obj.save()
        return obj


class NetworkUpdateSerializer(NetworkCreateSerializer):
    """Used for PUT, PATCH on Networks."""
    class Meta:
        model = models.Network
        fields = ('attributes',)

    def update(self, instance, validated_data):
        log.debug('NetworkUpdateSerializer.update() validated_data = %r',
                  validated_data)
        attributes = validated_data.pop('attributes', {})
        obj = super(NetworkUpdateSerializer, self).update(
            instance, validated_data
        )
        obj.set_attributes(attributes)
        obj.save()
        return obj


###########
# AuthToken
###########
class AuthTokenSerializer(serializers.Serializer):
    """
    AuthToken authentication serializer to validate username/secret_key inputs.
    """
    email = serializers.CharField()
    secret_key = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        secret_key = attrs.get('secret_key')

        if email and secret_key:
            auth_func = auth.SecretKeyAuthentication().authenticate_credentials
            user, secret_key = auth_func(email, secret_key)

            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise exc.ValidationError(msg)
                attrs['user'] = user
                return attrs
            else:
                msg = 'Unable to login with provided credentials.'
                raise exc.ValidationError(msg)
        else:
            msg = 'Must include "email" and "secret_key"'
            raise exc.ValidationError(msg)
