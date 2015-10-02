from __future__ import unicode_literals

import ast
from django.contrib.auth import get_user_model
from collections import OrderedDict
import json
import logging
from rest_framework import fields, serializers

from . import auth
from .. import exc, models
from ..util import get_field_attr


log = logging.getLogger(__name__)


###############
# Custom Fields
###############
class JSONDataField(fields.Field):
    """
    Base field used to represention attributes as JSON <-> ``field_type``.

    It is an error if ``field_type`` is not defined in a subclass.
    """
    field_type = None

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        log.debug('JSONDictField.to_internal_value() data = %r', data)
        if self.field_type is None:
            raise NotImplementedError(
                'You must subclass JSONDataField and define field_type'
            )

        if not data:
            data = self.field_type()

        if isinstance(data, self.field_type):
            return data

        # Try it as a regular JSON object
        try:
            return json.loads(data)
        except ValueError:
            # Or try it as a Python object
            try:
                return ast.literal_eval(data)
            except (SyntaxError, ValueError) as err:
                raise exc.ValidationError(err)
        except Exception as err:
            raise exc.ValidationError(err)
        return data


class JSONDictField(JSONDataField):
    """Field used to represention attributes as JSON <-> Dict."""
    field_type = dict


class JSONListField(JSONDataField):
    """Field used to represention attributes as JSON <-> List."""
    field_type = list


class NsotSerializer(serializers.ModelSerializer):
    attributes = JSONDictField(
        required=False,
        help_text='Dictionary of attributes to set.'
    )

    """Base serializer that logs change events."""
    def to_internal_value(self, data):
        """Inject site_pk from view's kwargs if it's not already in data."""
        kwargs = self.context['view'].kwargs

        log.debug(
            'NsotSerializer.to_internal_value() data [before] = %r', data
        )

        if 'site_id' not in data and 'site_pk' in kwargs:
            data['site_id'] = kwargs['site_pk']

        log.debug('NsotSerializer.to_internal_value() data [after] = %r', data)

        return super(NsotSerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        """Always return the dict representation."""
        if isinstance(obj, OrderedDict):
            return obj
        return obj.to_dict()


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
        self.with_secret_key = kwargs.pop('with_secret_key', None)
        super(UserSerializer, self).__init__(*args, **kwargs)

        # If we haven't passed `with_secret_key`, don't show the secret_key
        # field.
        if self.with_secret_key is None:
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


#########
# Changes
#########
class ChangeSerializer(NsotSerializer):
    """Used for displaying Change events."""
    class Meta:
        model = models.Change


###########
# Attribute
###########
class AttributeSerializer(NsotSerializer):
    """Used for GET, DELETE on Attributes."""
    class Meta:
        model = models.Attribute
        exclude = ('attributes',)


class AttributeCreateSerializer(AttributeSerializer):
    """Used for POST on Attributes."""
    constraints = JSONDictField(required=False)
    site_id = fields.IntegerField()

    class Meta:
        model = models.Attribute
        fields = ('name', 'description', 'resource_name', 'required',
                  'display', 'multi', 'constraints', 'site_id')


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


class DeviceCreateSerializer(DeviceSerializer):
    """Used for POST on Devices."""
    site_id = fields.IntegerField()

    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes', 'site_id')

    def create(self, validated_data):

        # Remove the related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        # Save the base object to the database.
        obj = super(DeviceCreateSerializer, self).create(validated_data)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            obj.save()

        return obj


class DeviceUpdateSerializer(DeviceCreateSerializer):
    """Used for PUT, PATCH, on Devices."""
    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes')

    def update(self, instance, validated_data):

        # Remove related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        # Save the object to the database.
        obj = super(DeviceUpdateSerializer, self).update(
            instance, validated_data
        )

        # Populate the related fields and save the object, allowing any
        # validation errors to raise before saving.
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


class NetworkCreateSerializer(NetworkSerializer):
    """Used for POST on Networks."""
    cidr = fields.CharField(write_only=True)
    site_id = fields.IntegerField()

    class Meta:
        model = models.Network
        fields = ('cidr', 'attributes', 'site_id')

    def create(self, validated_data):

        # Remove the related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        obj = super(NetworkCreateSerializer, self).create(validated_data)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
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

        # Remove related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        # Save the object to the database.
        obj = super(NetworkUpdateSerializer, self).update(
            instance, validated_data
        )

        # Populate the related fields and save the object, allowing any
        # validation errors to raise before saving.
        obj.set_attributes(attributes)
        obj.save()

        return obj


###########
# Interface
###########
class InterfaceSerializer(NsotSerializer):
    """Used for GET, DELETE on Interfaces."""
    parent_id = fields.IntegerField(
        required=False,
        label=get_field_attr(models.Interface, 'parent', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'parent', 'help_text'),
    )

    class Meta:
        model = models.Interface


class InterfaceCreateSerializer(InterfaceSerializer):
    """Used for POST on Interfaces."""
    addresses = JSONListField(
        required=False, help_text='List of host addresses to assign.'
    )
    mac_address = fields.CharField(
        required=False,
        label=get_field_attr(models.Interface, 'mac_address', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'mac_address', 'help_text'),
    )

    class Meta:
        model = models.Interface
        fields = ('device', 'name', 'description', 'type', 'mac_address',
                  'speed', 'parent_id', 'addresses', 'attributes')

    def create(self, validated_data):
        log.debug('InterfaceCreateSerializer.create() validated_data = %r',
                  validated_data)

        # Remove the related fields before we write the object
        attributes = validated_data.pop('attributes', {})
        addresses = validated_data.pop('addresses', [])

        # Forcefully set the Site for this object to that of the parent Device.
        validated_data['site'] = validated_data['device'].site

        # Save the base object to the database.
        obj = super(InterfaceCreateSerializer, self).create(validated_data)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_attributes(attributes)
            obj.set_addresses(addresses)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            obj.save()

        return obj


class InterfaceUpdateSerializer(InterfaceCreateSerializer):
    "Used for PUT, PATCH on Interfaces."""
    class Meta:
        model = models.Interface
        fields = ('name', 'description', 'type', 'mac_address', 'speed',
                  'parent', 'addresses', 'attributes')

    def update(self, instance, validated_data):
        log.debug('InterfaceUpdateSerializer.update() validated_data = %r',
                  validated_data)

        # Remove related fields before we write the object
        attributes = validated_data.pop('attributes', {})
        addresses = validated_data.pop('addresses', [])

        # Save the object to the database.
        obj = super(InterfaceUpdateSerializer, self).update(
            instance, validated_data
        )

        # Populate the related fields and save the object, allowing any
        # validation errors to raise before saving.
        obj.set_attributes(attributes)
        obj.set_addresses(addresses, overwrite=True)
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
