from __future__ import unicode_literals
import ast
from collections import OrderedDict
import json
import logging

from django.contrib.auth import get_user_model
from rest_framework import fields, serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

from . import auth
from .. import exc, models, validators
from ..util import get_field_attr


log = logging.getLogger(__name__)


###############
# Custom Fields
###############
class JSONDataField(fields.Field):
    """
    Base field used to represent attributes as JSON <-> ``field_type``.

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
    """Field used to represent attributes as JSON <-> Dict."""
    field_type = dict


class JSONListField(JSONDataField):
    """Field used to represent attributes as JSON <-> List."""
    field_type = list


class MACAddressField(fields.Field):
    """Field used to validate MAC address objects as integer or string."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, value):
        return validators.validate_mac_address(value)


class NaturalKeyRelatedField(serializers.SlugRelatedField):
    """Field that takes either a primary key or a natural key."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, value):
        """Try PK followed by slug (natural key) value."""
        # Cast integers to strings, bruh
        if isinstance(value, int):
            value = str(value)

        # Is digit? Is PK.
        if value.isdigit():
            field = serializers.PrimaryKeyRelatedField(
                queryset=self.get_queryset()
            )
            log.debug(
                'NaturalKeyRelatedField: %s using PK field for value %s',
                self.field_name, value
            )
        # Or it's natural key. Brute force!!
        else:
            field = serializers.SlugRelatedField(
                slug_field=self.slug_field,
                queryset=self.get_queryset(),
            )
            log.debug(
                'NaturalKeyRelatedField: %s using SLUG field for value %s',
                self.field_name, value
            )

        value = field.to_internal_value(value)

        return value

    def get_queryset(self):
        """Attempt to filter queryset by site_pk."""
        queryset = super(NaturalKeyRelatedField, self).get_queryset()
        view = self.context.get('view')

        # Get site_id from the view or None
        if view is None:
            site_id = None
        else:
            site_id = view.kwargs.get('site_pk')

        # Filter by site_id if applicable.
        if site_id is not None:
            log.debug('Filtering queryset to site_id=%s', site_id)
            queryset = queryset.filter(site_id=site_id)

        return queryset


###################
# Base Serializer #
###################
class NsotSerializer(serializers.ModelSerializer):
    """Base serializer that logs change events."""
    def to_internal_value(self, data):
        """Inject site_pk from view's kwargs if it's not already in data."""
        # Try to get the kwargs from the view, or default to empty kwargs.
        view = self.context.get('view')
        kwargs = getattr(view, 'kwargs', {})

        log.debug(
            'NsotSerializer.to_internal_value() data [before] = %r', data
        )

        # FIXME(jathan): This MUST be ripped out once we migrate to V2 API and
        # move away from the "site_id" field on pre-1.0 objects.
        site_fields = ['site_id', 'site']
        for site_field in site_fields:
            if site_field in self.fields:
                break
        else:
            site_field = None

        if site_field not in data and 'site_pk' in kwargs:
            data = data.copy()  # Get a mutable copy of the QueryDict
            data[site_field] = kwargs['site_pk']

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
        fields = '__all__'


#########
# Changes
#########
class ChangeSerializer(NsotSerializer):
    """Used for displaying Change events."""
    class Meta:
        model = models.Change
        fields = '__all__'


###########
# Attribute
###########
class AttributeSerializer(NsotSerializer):
    """Used for GET, DELETE on Attributes."""
    class Meta:
        model = models.Attribute
        fields = '__all__'


class AttributeCreateSerializer(AttributeSerializer):
    """Used for POST on Attributes."""
    constraints = JSONDictField(
        required=False,
        label=get_field_attr(models.Attribute, 'constraints', 'verbose_name'),
        help_text=get_field_attr(models.Attribute, 'constraints', 'help_text')
    )
    site_id = fields.IntegerField(
        label=get_field_attr(models.Attribute, 'site', 'verbose_name'),
        help_text=get_field_attr(models.Attribute, 'site', 'help_text')
    )

    class Meta:
        model = models.Attribute
        fields = ('name', 'description', 'resource_name', 'required',
                  'display', 'multi', 'constraints', 'site_id')


class AttributeUpdateSerializer(BulkSerializerMixin,
                                AttributeCreateSerializer):
    """
    Used for PUT, PATCH, on Attributes.

    Currently because Attributes have only one required field (name), and it
    may not be updated, there is not much functional difference between PUT and
    PATCH.
    """
    class Meta:
        model = models.Attribute
        list_serializer_class = BulkListSerializer
        fields = ('id', 'description', 'required', 'display', 'multi',
                  'constraints')


#######
# Value
#######
class ValueSerializer(serializers.ModelSerializer):
    """Used for GET, DELETE on Values."""
    class Meta:
        model = models.Value
        fields = ('id', 'name', 'value', 'attribute', 'resource_name',
                  'resource_id')


class ValueCreateSerializer(ValueSerializer):
    """Used for POST on Values."""
    class Meta(ValueSerializer.Meta):
        read_only_fields = ('id', 'name', 'resource_name')


###########
# Resources
###########
class ResourceSerializer(NsotSerializer):
    """For any object that can have attributes."""
    attributes = JSONDictField(
        required=False,
        help_text='Dictionary of attributes to set.'
    )
    site_id = serializers.PrimaryKeyRelatedField(
        source='site', queryset=models.Site.objects.all(),
        help_text='Unique ID of the Site this object is under.',
        label='Site',
    )

    def create(self, validated_data, commit=True):
        """Create that is aware of attributes."""
        # Remove the related fields before we write the object
        attributes = validated_data.pop('attributes', {})

        # Save the base object to the database.
        obj = super(ResourceSerializer, self).create(validated_data)

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_attributes(attributes)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            if commit:
                obj.save()

        return obj

    def update(self, instance, validated_data, commit=True):
        """
        Update that is aware of attributes.

        This will not set attributes if they are not provided during a partial
        update.
        """
        # Remove related fields before we write the object
        attributes = validated_data.pop('attributes', None)

        # Save the object to the database.
        obj = super(ResourceSerializer, self).update(
            instance, validated_data
        )

        # If attributes have been provided, populate them and save the object,
        # allowing any validation errors to raise before saving.
        obj.set_attributes(attributes, partial=self.partial)

        if commit:
            obj.save()

        return obj


########
# Device
########
class DeviceSerializer(ResourceSerializer):
    """Used for GET, DELETE on Devices."""

    class Meta:
        model = models.Device
        fields = '__all__'


class DeviceCreateSerializer(DeviceSerializer):
    """Used for POST on Devices."""

    class Meta:
        model = models.Device
        fields = ('hostname', 'attributes', 'site_id')


class DevicePartialUpdateSerializer(BulkSerializerMixin,
                                    DeviceCreateSerializer):
    """Used for PATCH on Devices."""
    class Meta:
        model = models.Device
        list_serializer_class = BulkListSerializer
        fields = ('id', 'hostname', 'attributes')


class DeviceUpdateSerializer(DevicePartialUpdateSerializer):
    """Used for PUT on Devices."""

    class Meta(DevicePartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


#########
# Network
#########
class NetworkSerializer(ResourceSerializer):
    """Used for GET, DELETE on Networks."""

    class Meta:
        model = models.Network
        fields = '__all__'


class NetworkCreateSerializer(NetworkSerializer):
    """Used for POST on Networks."""
    cidr = fields.CharField(
        write_only=True, required=False, label='CIDR',
        help_text=(
            'IPv4/IPv6 CIDR address. If provided, this overrides the value of '
            'network_address & prefix_length. If not provided, '
            'network_address & prefix_length are required.'
        )
    )

    class Meta:
        model = models.Network
        fields = ('cidr', 'network_address', 'prefix_length', 'attributes',
                  'state', 'site_id')
        extra_kwargs = {
            'network_address': {'required': False},
            'prefix_length': {'required': False},
        }


class NetworkPartialUpdateSerializer(BulkSerializerMixin,
                                     NetworkCreateSerializer):
    """Used for PATCH on Networks."""

    class Meta:
        model = models.Network
        list_serializer_class = BulkListSerializer
        fields = ('id', 'attributes', 'state')


class NetworkUpdateSerializer(NetworkPartialUpdateSerializer):
    """Used for PUT on Networks."""

    class Meta(NetworkPartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


###########
# Interface
###########
class InterfaceSerializer(ResourceSerializer):
    """Used for GET, DELETE on Interfaces."""
    parent_id = NaturalKeyRelatedField(
        required=False, allow_null=True,
        slug_field='name_slug',
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Interface, 'parent', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'parent', 'help_text'),
    )
    device = NaturalKeyRelatedField(
        slug_field='hostname',
        queryset=models.Device.objects.all(),
        label=get_field_attr(models.Interface, 'device', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'device', 'help_text'),
    )
    addresses = JSONListField(
        required=False, help_text='List of host addresses to assign.'
    )
    mac_address = MACAddressField(
        required=False, allow_null=True,
        label=get_field_attr(models.Interface, 'mac_address', 'verbose_name'),
        help_text=get_field_attr(models.Interface, 'mac_address', 'help_text'),
    )

    class Meta:
        model = models.Interface
        fields = '__all__'

    def validate_parent_id(self, value):
        """Cast the parent_id to an int if it's an Interface object."""
        # FIXME(jathan): Remove this hackery when we move away from `parent_id`
        # to `parent` in the future.
        if value is not None and isinstance(value, models.Interface):
            return value.id

        return value

    def create(self, validated_data):
        """Overload default create to handle setting of addresses."""
        log.debug('InterfaceCreateSerializer.create() validated_data = %r',
                  validated_data)

        # Remove the related fields before we write the object
        addresses = validated_data.pop('addresses', [])

        # Create the base object to the database, but don't save attributes
        # yet.
        obj = super(InterfaceSerializer, self).create(
            validated_data, commit=False
        )

        # Try to populate the related fields and if there are any validation
        # problems, delete the object and re-raise the error. If not, save the
        # changes.
        try:
            obj.set_addresses(addresses)
        except exc.ValidationError:
            obj.delete()
            raise
        else:
            obj.save()

        return obj

    def update(self, instance, validated_data):
        """Overload default update to handle setting of addresses."""
        log.debug('InterfaceUpdateSerializer.update() validated_data = %r',
                  validated_data)

        # Remove related fields before we write the object. Attributes are
        # handled by the parent.
        addresses = validated_data.pop('addresses', None)

        # Update the attributes in the database, but don't save them yet.
        obj = super(InterfaceSerializer, self).update(
            instance, validated_data, commit=False
        )

        # Assign the address objects to the Interface.
        obj.set_addresses(addresses, overwrite=True, partial=self.partial)
        obj.save()

        return obj


class InterfaceCreateSerializer(InterfaceSerializer):
    """Used for POST on Interfaces."""

    class Meta:
        model = models.Interface
        fields = ('device', 'name', 'description', 'type', 'mac_address',
                  'speed', 'parent_id', 'addresses', 'attributes')


class InterfacePartialUpdateSerializer(BulkSerializerMixin,
                                       InterfaceCreateSerializer):
    "Used for PATCH on Interfaces."""
    class Meta:
        model = models.Interface
        list_serializer_class = BulkListSerializer
        fields = ('id', 'name', 'description', 'type', 'mac_address', 'speed',
                  'parent_id', 'addresses', 'attributes')


class InterfaceUpdateSerializer(InterfacePartialUpdateSerializer):
    "Used for PUT on Interfaces."""

    class Meta(InterfacePartialUpdateSerializer.Meta):
        extra_kwargs = {
            'addresses': {'required': True},
            'attributes': {'required': True},
        }


#########
# Circuit
#########
class CircuitSerializer(ResourceSerializer):
    """Used for GET, DELETE on Circuits"""
    endpoint_a = NaturalKeyRelatedField(
        slug_field='name_slug',
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, 'endpoint_a', 'verbose_name'),
        help_text=get_field_attr(models.Circuit, 'endpoint_a', 'help_text'),
    )
    endpoint_z = NaturalKeyRelatedField(
        slug_field='name_slug',
        required=False, allow_null=True,
        queryset=models.Interface.objects.all(),
        label=get_field_attr(models.Circuit, 'endpoint_z', 'verbose_name'),
        help_text=get_field_attr(models.Circuit, 'endpoint_z', 'help_text'),
    )

    class Meta:
        model = models.Circuit
        fields = '__all__'


class CircuitCreateSerializer(CircuitSerializer):
    """Used for POST on Circuits."""

    class Meta:
        model = models.Circuit
        # Display name and site are auto-generated, don't include them here.
        fields = ('endpoint_a', 'endpoint_z', 'name', 'attributes')


class CircuitPartialUpdateSerializer(BulkSerializerMixin,
                                     CircuitCreateSerializer):
    """Used for PATCH on Circuits."""
    class Meta:
        model = models.Circuit
        list_serializer_class = BulkListSerializer
        fields = ('id', 'endpoint_a', 'endpoint_z', 'name', 'attributes')


class CircuitUpdateSerializer(CircuitPartialUpdateSerializer):
    """Used for PUT on Circuits."""

    class Meta(CircuitPartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


##############
# ProtocolType
##############
class ProtocolTypeSerializer(NsotSerializer):
    """Used for all CRUD operations on ProtocolTypes."""
    required_attributes = NaturalKeyRelatedField(
        many=True, slug_field='name', required=False,
        queryset=models.Attribute.objects.all(),
        help_text=get_field_attr(
            models.ProtocolType, 'required_attributes', 'help_text'
        ),
    )

    class Meta:
        model = models.ProtocolType
        fields = '__all__'


##########
# Protocol
##########
class ProtocolSerializer(ResourceSerializer):
    """Used for GET, DELETE on Protocols"""
    type = NaturalKeyRelatedField(
        slug_field='name',
        queryset=models.ProtocolType.objects.all(),
        help_text=get_field_attr(models.Protocol, 'type', 'help_text'),
    )
    device = NaturalKeyRelatedField(
        slug_field='hostname',
        queryset=models.Device.objects.all(),
        help_text=get_field_attr(models.Protocol, 'device', 'help_text'),
    )
    interface = NaturalKeyRelatedField(
        slug_field='name_slug',
        required=False, allow_null=True,
        queryset=models.Interface.objects.all(),
        help_text=get_field_attr(models.Protocol, 'interface', 'help_text'),
    )
    circuit = NaturalKeyRelatedField(
        slug_field='name_slug',
        required=False, allow_null=True,
        queryset=models.Circuit.objects.all(),
        help_text=get_field_attr(models.Protocol, 'circuit', 'help_text'),
    )

    class Meta:
        model = models.Protocol
        fields = '__all__'


class ProtocolCreateSerializer(ProtocolSerializer):
    """Used for POST on Protocols."""
    class Meta:
        model = models.Protocol
        fields = ('site', 'type', 'device', 'description', 'auth_string',
                  'interface', 'circuit', 'attributes')


class ProtocolPartialUpdateSerializer(BulkSerializerMixin,
                                      ProtocolCreateSerializer):
    """Used for PATCH on Protocols."""
    class Meta:
        model = models.Protocol
        list_serializer_class = BulkListSerializer
        fields = ('id', 'site', 'type', 'device', 'description', 'auth_string',
                  'interface', 'circuit', 'attributes')


class ProtocolUpdateSerializer(ProtocolPartialUpdateSerializer):
    """Used for PUT on Protocols."""

    class Meta(ProtocolPartialUpdateSerializer.Meta):
        extra_kwargs = {'attributes': {'required': True}}


###########
# AuthToken
###########
class AuthTokenSerializer(serializers.Serializer):
    """
    AuthToken authentication serializer to validate username/secret_key inputs.
    """
    email = serializers.CharField(help_text='Email address of the user.')
    secret_key = serializers.CharField(
        label='Secret Key', help_text='Secret key of the user.'
    )

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
