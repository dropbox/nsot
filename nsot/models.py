from __future__ import unicode_literals

from calendar import timegm
from cryptography.fernet import (Fernet, InvalidToken)
from datetime import datetime
from email.utils import parseaddr
from operator import attrgetter
import functools
import ipaddress
import re
import json
import logging
import time

from sqlalchemy import create_engine, or_, union_all, desc
from sqlalchemy.event import listen
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, aliased, validates
from sqlalchemy.orm import synonym, sessionmaker, Session as _Session, backref
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.sql import func, label, literal, false
from sqlalchemy.types import Integer, String, Text, Boolean, SmallInteger
from sqlalchemy.types import Enum, DateTime, VARBINARY

from . import constants
from . import exc
from .permissions import PermissionsFlag
from .settings import settings


log = logging.getLogger(__name__)

RESOURCE_BY_IDX = (
    "Site", "Network", "Attribute", "Permission", "Device"
)
RESOURCE_BY_NAME = {
    obj_type: idx
    for idx, obj_type in enumerate(RESOURCE_BY_IDX)
}

CHANGE_EVENTS = ("Create", "Update", "Delete")
IP_VERSIONS = ("4", "6")


VALID_CHANGE_RESOURCES = set(RESOURCE_BY_IDX)
VALID_ATTRIBUTE_RESOURCES = set([
    "Network", "Device",
])


class Session(_Session):
    """ Custom session meant to utilize add on the model.

        This Session overrides the add/add_all methods to prevent them
        from being used. This is to for using the add methods on the
        models themselves where overriding is available.
    """

    _add = _Session.add
    _add_all = _Session.add_all
    _delete = _Session.delete

    def add(self, *args, **kwargs):
        raise NotImplementedError("Use add method on models instead.")

    def add_all(self, *args, **kwargs):
        raise NotImplementedError("Use add method on models instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Use delete method on models instead.")


Session = sessionmaker(class_=Session)

class Model(object):
    """ Custom model mixin with helper methods. """

    def __repr__(self):
        cls_name = self.__class__.__name__
        return u'%s(id=%r)' % (cls_name, self.id)

    @property
    def session(self):
        return object_session(self)

    @classmethod
    def query(cls):
        """Return a Query using session defaults."""
        # The Model.query() method doesn't work on classmethods. We need a
        # scoped_session for that
        from .meta import ScopedSession
        return ScopedSession().query(cls)

    @classmethod
    def get_or_create(cls, session, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).scalar()
        if instance:
            return instance, False

        instance = cls(**kwargs)
        instance.add(session)

        return instance, True

    @property
    def model_name(self):
        obj_name = type(self).__name__
        return obj_name

    @classmethod
    def before_create(cls, session, user_id):
        """ Hook for before object creation."""

    def after_create(self, user_id):
        """ Hook for after object creation."""

    @classmethod
    def create(cls, session, _user_id, **kwargs):
        commit = kwargs.pop("commit", True)
        try:
            cls.before_create(session, _user_id)
            obj = cls(**kwargs).add(session)
            session.flush()
            obj.after_create(_user_id)
            Change.create(session, _user_id, "Create", obj)
            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise

        return obj

    def update(self, user_id, **kwargs):
        session = self.session
        try:
            for key, value in kwargs.iteritems():
                setattr(self, key, value)

            session.flush()
            Change.create(session, user_id, "Update", self)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def add(self, session):
        session._add(self)
        return self

    def before_delete(self):
        """ Hook for extra model cleanup before delete. """

    def after_delete(self):
        """ Hook for extra model cleanup after delete. """

    def delete(self, user_id):
        session = self.session
        try:
            Change.create(session, user_id, "Delete", self)
            self.before_delete()
            session._delete(self)
            self.after_delete()
            session.commit()
        except Exception:
            session.rollback()
            raise


Model = declarative_base(cls=Model)


# Foreign Keys are ignored by default in SQLite. Don't do that.
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def get_db_engine(url, echo=False):
    engine = create_engine(url, pool_recycle=300, echo=echo)
    if engine.driver == "pysqlite":
        listen(engine, "connect", _set_sqlite_pragma)

    return engine


def get_db_session(db_engine=None, database=None):
    """
    Return a usable session object.

    If not provided, this will attempt to retreive the database and db_engine
    from settings. If settings have not been updated from a config, this will
    return ``None``.

    :param db_engine:
        Database engine to use

    :param database:
        URI for database
    """
    if database is None:
        database = settings.database
        if database is None:
            return None
    if db_engine is None:
        db_engine = get_db_engine(database)
    Session.configure(bind=db_engine)
    return Session()


def flush_transaction(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        dryrun = kwargs.pop("dryrun", False)
        try:
            ret = method(self, *args, **kwargs)
            if dryrun:
                self.session.rollback()
            else:
                self.session.flush()
        except Exception:
            log.exception("Transaction Failed. Rolling back.")
            if self.session is not None:
                self.session.rollback()
            raise
        return ret
    return wrapper


class User(Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(length=255), unique=True, nullable=False)

    # The user's secret key is used to generate their auth_token
    secret_key = Column(String(length=255), default=Fernet.generate_key)

    @validates("email")
    def validate_email(self, key, value):
        _, email = parseaddr(value)
        if email == '' or "@" not in value:
            raise exc.ValidationError("Must contain a valid e-mail address")
        return value

    def to_dict(self, with_permissions=False, with_secret_key=False):
        out = {
            "id": self.id,
            "email": self.email,
        }

        if with_secret_key:
            out["secret_key"] = self.secret_key

        if with_permissions:
            out["permissions"] = self.get_permissions()

        return out

    def rotate_secret_key(self):
        self.secret_key = Fernet.generate_key()

    def get_permissions(self, site_id=None):
        query = self.session.query(Permission).filter_by(
            user_id=self.id
        )

        if site_id is not None:
            query = query.filter_by(site_id=site_id)

        permissions = query.all()

        return {
            # JSON keys can't be ints so be consistent in
            # python
            str(permission.site_id): permission.to_dict()
            for permission in permissions
        }

    def generate_auth_token(self):
        """Serialize user data and encrypt token."""
        # Serialize data
        data = json.dumps({'email': self.email })

        # Encrypt w/ servers's secret_key
        f = Fernet(bytes(settings.secret_key))
        auth_token = f.encrypt(bytes(data))
        return auth_token

    def verify_secret_key(self, secret_key):
        """Validate secret_key"""
        return secret_key == self.secret_key

    @classmethod
    def verify_auth_token(cls, email, auth_token,
                          expiration=None, session=None):
        """Verify token and return a User object."""
        if expiration is None:
            expiration = settings.auth_token_expiry

        # First we lookup the user by email
        if session is None:
            query = User.query()
        else:
            query = session.query(User)
        user = query.filter_by(email=email).scalar()

        if user is None:
            log.debug('Invalid user when verifying token')
            return None  # Invalid user

        # Decrypt auth_token w/ user's secret_key
        f = Fernet(bytes(settings.secret_key))
        try:
            decrypted_data = f.decrypt(bytes(auth_token), ttl=expiration)
        except InvalidToken:
            log.debug('Invalid/expired auth_token when decrypting.')
            return None  # Invalid token

        # Deserialize data
        try:
            data = json.loads(decrypted_data)
        except ValueError:
            log.debug('Token could not be deserialized.')
            return None  # Valid token, but expired

        if email != data['email']:
            log.debug('Invalid user when deserializing.')
            return None  # User email did not match payload
        return user


class Permission(Model):
    __tablename__ = "permissions"
    __table_args__ = (
        Index("site_user_idx", "site_id", "user_id", unique=True),
    )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    permissions_flag = Column(Integer, default=0, nullable=False)

    @property
    def permissions(self):
        perms = []
        flag = PermissionsFlag(self.permissions_flag)
        for word in PermissionsFlag.words:
            if flag.has(word):
                perms.append(word)
        return perms

    @permissions.setter
    def permissions(self, value):
        flag = PermissionsFlag()
        for word in value:
            flag.set(word)
        self.permissions_flag = flag.dump()

    def to_dict(self):
        return {
            # Not including primary key here since all operations
            # will be on the composite key of site_id and user_id.
            "site_id": self.site_id,
            "user_id": self.user_id,
            "permissions": self.permissions,
        }


class Site(Model):
    """ A namespace for subnets, ipaddresses, attributes. """

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), unique=True, nullable=False)
    description = Column(Text, default="", nullable=False)

    # All generic resources are expected to have a site_id attribute.
    site_id = synonym("id")


    def after_create(self, user_id):
        Permission.create(
            self.session, user_id, site_id=self.id, user_id=user_id,
            permissions=["admin"]
        )

    def devices(self, attribute_name=None, attribute_value=None):
        """ Helper method for grabbing Networks.

            Args:
                attribute_name: Filter to networks that contain this attribute name
                attribute_value: Filter to networks that contain this attribute value
        """

        if attribute_value is not None and attribute_name is None:
            raise ValueError("attribute_value requires attribute_name to be set.")

        query = self.session.query(Device)

        if attribute_name is not None:
            query = query.outerjoin(Device.attr_idx).filter(
                DeviceAttributeIndex.name == attribute_name
            )
            if attribute_value is not None:
                query = query.filter(DeviceAttributeIndex.value == attribute_value)

        query = query.filter(Device.site_id==self.id)

        return query

    def networks(self, include_networks=True, include_ips=False, root=False,
                 subnets_of=None, supernets_of=None,
                 attribute_name=None, attribute_value=None):
        """ Helper method for grabbing Networks.

            Args:
                include_networks: Whether the response should include non-ip
                                  address networks
                include_ips: Whether the response should include ip addresses
                root: Only return networks at the root.
                subnets_of: Only return subnets of the given CIDR
                supernets_of: Only return supernets of the given CIDR
                attribute_name: Filter to networks that contain this attribute name
                attribute_value: Filter to networks that contain this attribute value
        """

        if not any([include_networks, include_ips]):
            return self.session.query(Network).filter(false())

        if attribute_value is not None and attribute_name is None:
            raise ValueError("attribute_value requires attribute_name to be set.")

        if all([subnets_of, supernets_of]):
            raise ValueError("subnets_of and supernets_of are mutually exclusive.")

        query = self.session.query(Network)

        if attribute_name is not None:
            query = query.outerjoin(Network.attr_idx).filter(
                NetworkAttributeIndex.name == attribute_name
            )
            if attribute_value is not None:
                query = query.filter(NetworkAttributeIndex.value == attribute_value)

        query = query.filter(Network.site_id==self.id)

        if not all([include_networks, include_ips]):
            if include_networks:
                query = query.filter(Network.is_ip == False)
            if include_ips:
                query = query.filter(Network.is_ip == True)

        if root:
            query = query.filter(Network.parent_id == None)

        if subnets_of is not None:
            subnets_of = ipaddress.ip_network(unicode(subnets_of))
            query = query.filter(
                Network.ip_version == str(subnets_of.version),
                Network.prefix_length > subnets_of.prefixlen,
                Network.network_address >= subnets_of.network_address.packed,
                Network.broadcast_address <= subnets_of.broadcast_address.packed
            )

        if supernets_of is not None:
            supernets_of = ipaddress.ip_network(unicode(supernets_of))
            query = query.filter(
                Network.ip_version == str(supernets_of.version),
                Network.prefix_length < supernets_of.prefixlen,
                Network.network_address <= supernets_of.network_address.packed,
                Network.broadcast_address >= supernets_of.broadcast_address.packed
            )

        return query


    @validates("name")
    def validate_name(self, key, value):
        if not value:
            raise exc.ValidationError("Name is a required field.")
        return value


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


class AttributeIndexMixin(object):
    """ Shared columns for AttributeIndex tables. """
    id = Column(Integer, primary_key=True)

    name = Column(String(length=64), nullable=False, index=True)
    value = Column(String(length=255), nullable=False, index=True)

    @declared_attr
    def attribute_id(self):
        return Column(Integer, ForeignKey("attributes.id"), nullable=False)

    @declared_attr
    def attribute(self):
        return relationship("Attribute")


class NetworkAttributeIndex(AttributeIndexMixin, Model):
    """ An Inverted Index for looking up Networks by their attributes."""

    __tablename__ = "network_attribute_index"

    resource_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    resource = relationship("Network", backref="attr_idx")


class DeviceAttributeIndex(AttributeIndexMixin, Model):
    """ An Inverted Index for looking up Devices by their attributes."""

    __tablename__ = "device_attribute_index"

    resource_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    resource = relationship("Device", backref="attr_idx")


class AttributeModelMixin(object):
    """ Shared columns and methods for resources that support attributes. """

    # Attributes is a Serialized LOB field. Lookups of these attributes
    # is done against an Inverted Index table
    _attributes = Column("attributes", Text)

    def _purge_attribute_index(self):
        index_table = self._index_class.__table__
        self.session.execute(
            index_table.delete().where(index_table.c.resource_id == self.id)
        )

    def get_attributes(self):
        if self._attributes is None:
            return {}
        return json.loads(self._attributes)

    def set_attributes(self, attributes, valid_attributes=None):
        if not isinstance(attributes, dict):
            raise exc.ValidationError("Expected dictionary but received {}".format(
                type(attributes)
            ))

        if valid_attributes is None:
            valid_attributes = Attribute.all_by_name(self.session, self._resource_name)

        missing_attributes = {
            attribute.name
            for attribute in valid_attributes.itervalues()
            if attribute.required and attribute.name not in attributes
        }

        if missing_attributes:
            raise exc.ValidationError("Missing required attributes: {}".format(
                ", ".join(missing_attributes)
            ))

        inserts = []
        for name, value in attributes.iteritems():
            if name not in valid_attributes:
                raise exc.ValidationError("Attribute name ({}) does not exist.".format(
                    name
                ))

            if not isinstance(name, basestring):
                raise exc.ValidationError("Attribute names must be a string type")

            attribute = valid_attributes[name]
            inserts.extend(attribute.validate_value(value))

        for insert in inserts:
            insert["resource_id"] = self.id

        self._purge_attribute_index()
        if inserts:
            index_table = self._index_class.__table__
            self.session.execute(index_table.insert(), inserts)

        self._attributes = json.dumps(attributes)

    def update(self, user_id, **kwargs):
        session = self.session
        try:
            for key, value in kwargs.iteritems():
                if key == "attributes":
                    self.set_attributes(value)
                else:
                    setattr(self, key, value)
            session.flush()
            Change.create(session, user_id, "Update", self)
            session.commit()
        except Exception:
            session.rollback()
            raise


class Device(AttributeModelMixin, Model):
    """ Represents a network device. """

    # Class attributes used by Mixin
    _index_class = DeviceAttributeIndex
    _resource_name = "Device"

    __tablename__ = "devices"
    __table_args__ = (
        Index(
            "hostname_idx",
            "site_id", "hostname",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    hostname = Column(String(255), nullable=False, index=True)

    @classmethod
    def create(cls, session, user_id, site_id, hostname, attributes=None, **kwargs):

        # TODO(gary): Decent duplication between Device and  Network create method.
        #             Clean this up at some point.
        commit = kwargs.pop("commit", True)
        if attributes is None:
            attributes = {}

        try:
            obj = cls(site_id=site_id, hostname=hostname)
            obj.add(session)
            # Need to get a primary key for the new network to update subnets.
            session.flush()
            # Attributes have to be added after the initial flush since we need the
            # id to setup the inverted index. This will mean we have to send another
            # update later. This could be improved by separating the index step but
            # probably isn't worth it.
            obj.set_attributes(attributes)
            Change.create(session, user_id, "Create", obj)

            if commit:
                session.commit()

        except Exception:
            session.rollback()
            raise

        return obj

    @validates("hostname")
    def validate_hostname(self, key, value):
        if not value:
            raise exc.ValidationError("hostname must be non-zero length string.")
        return value

    def before_delete(self):
        self._purge_attribute_index()

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "hostname": self.hostname,
            "attributes": self.get_attributes(),
        }


class Network(AttributeModelMixin, Model):
    """ Represents a subnet or ipaddress. """

    # Class attributes used by Mixin
    _index_class = NetworkAttributeIndex
    _resource_name = "Network"

    __tablename__ = "networks"
    __table_args__ = (
        Index(
            "cidr_idx",
            "site_id", "ip_version", "network_address", "prefix_length",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)

    ip_version = Column(String(1), nullable=False, index=True)

    # Root networks will be NULL while other networks will point to
    # their supernet.
    parent_id = Column(Integer, ForeignKey("networks.id"), nullable=True)

    network_address = Column(VARBINARY(16), nullable=False, index=True)
    # While derivable from network/prefix this is useful as it enables
    # easy querys of the nested set variety.
    broadcast_address = Column(VARBINARY(16), nullable=False, index=True)

    prefix_length = Column(Integer, nullable=False, index=True)

    # Simple boolean
    is_ip = Column(Boolean, nullable=False, default=False, index=True)

    @validates("ip_version")
    def validate_ip_version(self, key, value):
        if value not in IP_VERSIONS:
            raise exc.ValidationError("Invalid IP Version.")
        return value

    def to_dict(self):
        network_address = ipaddress.ip_address(self.network_address)

        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "site_id": self.site_id,
            "is_ip": self.is_ip,
            "ip_version": self.ip_version,
            "network_address": network_address.exploded,
            "prefix_length": self.prefix_length,
            "attributes": self.get_attributes(),
        }

    def before_delete(self):
        self._purge_attribute_index()

    def supernets(self, session, direct=False, discover_mode=False, for_update=False):
        """ Get networks that are a supernet of a network.

            Args:
                direct: Only return direct supernet.
                discover_mode: Prevent new networks from bailing for missing parent_id
                for_update: Lock these rows because they're selected for updating.

        """

        if self.parent_id is None and not discover_mode:
            return self.session.query(Network).filter(false())

        if discover_mode and direct:
            raise ValueError("direct is incompatible with discover_mode")

        query = session.query(Network)
        if for_update:
            query = query.with_for_update()

        if direct:
            return query.filter(Network.id == self.parent_id)

        return query.filter(
            Network.is_ip == False,
            Network.ip_version == self.ip_version,
            Network.prefix_length < self.prefix_length,
            Network.network_address <= self.network_address,
            Network.broadcast_address >= self.broadcast_address
        )

    def subnets(self, session, include_networks=True, include_ips=False,
                direct=False, for_update=False):
        """ Get networks that are subnets of a network.

            Args:
                include_networks: Whether the response should include non-ip address networks
                include_ips: Whether the response should include ip addresses
                direct: Only return direct subnets.
                for_update: Lock these rows because they're selected for updating.
        """

        if not any([include_networks, include_ips]) or self.is_ip:
            return self.session.query(Network).filter(false())

        query = session.query(Network)
        if for_update:
            query = query.with_for_update()

        if not all([include_networks, include_ips]):
            if include_networks:
                query = query.filter(Network.is_ip == False)
            if include_ips:
                query = query.filter(Network.is_ip == True)

        if direct:
            return query.filter(Network.parent_id == self.id)

        return query.filter(
            Network.site_id == self.site_id,
            Network.ip_version == self.ip_version,
            Network.prefix_length > self.prefix_length,
            Network.network_address >= self.network_address,
            Network.broadcast_address <= self.broadcast_address
        )

    @property
    def cidr(self):
        return u"{}/{}".format(
            ipaddress.ip_address(self.network_address).exploded,
            self.prefix_length
        )
    @property
    def ip_network(self):
        return ipaddress.ip_network(self.cidr)

    def __repr__(self):
        return "Network<{}>".format(self.cidr)

    def reparent_subnets(self, session):
        query = session.query(Network).with_for_update().filter(
            Network.parent_id == self.parent_id,
            Network.id != self.id,  # Don't include yourself...
            Network.prefix_length > self.prefix_length,
            Network.ip_version == self.ip_version,
            Network.network_address >= self.network_address,
            Network.broadcast_address <= self.broadcast_address
        )

        query.update({Network.parent_id: self.id})

    @classmethod
    def create(cls, session, user_id, site_id, cidr, attributes=None, **kwargs):
        commit = kwargs.pop("commit", True)
        if attributes is None:
            attributes = {}
        if not cidr:
            msg = "Invalid CIDR: {}. Must be IPv4/IPv6 notation.".format(cidr)
            raise exc.ValidationError(msg)

        network = cidr
        if isinstance(cidr, unicode):
            network = ipaddress.ip_network(cidr)

        is_ip = False
        if network.network_address == network.broadcast_address:
            is_ip = True

        kwargs = {
            "site_id": site_id,
            "ip_version": str(network.version),
            "network_address": network.network_address.packed,
            "broadcast_address": network.broadcast_address.packed,
            "prefix_length": network.prefixlen,
            "is_ip": is_ip,
        }

        try:
            obj = cls(**kwargs)
            obj.add(session)
            # Need to get a primary key for the new network to update subnets.
            session.flush()
            # Attributes have to be added after the initial flush since we need the
            # id to setup the inverted index. This will mean we have to send another
            # update later. This could be improved by separating the index step but
            # probably isn't worth it.
            obj.set_attributes(attributes)

            supernets = obj.supernets(session, discover_mode=True, for_update=True).all()
            if supernets:
                parent = max(supernets, key=attrgetter("prefix_length"))
                obj.parent_id = parent.id

            if obj.parent_id is None and is_ip:
                raise exc.ValidationError("IP Address needs base network.")

            if not is_ip:
                obj.reparent_subnets(session)

            session.flush()
            Change.create(session, user_id, "Create", obj)

            if commit:
                session.commit()
        except Exception:
            session.rollback()
            raise

        return obj

class Attribute(Model):

    __tablename__ = "attributes"
    __table_args__ = (
        Index(
            "name_idx",
            "site_id", "resource_name", "name",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)

    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    resource_name = Column(String(20), nullable=False, index=True)

    # This is purposely not unique as there is a compound index with site_id.
    name = Column(String(length=64), nullable=False)
    description = Column(Text, default="", nullable=False)

    # The resource must contain a key and value
    required = Column(Boolean, default=False, nullable=False)

    # In UIs this attribute will be displayed by default.
    # required implies display.
    display = Column(Boolean, default=False, nullable=False)

    # Attribute values are expected as lists of strings.
    multi = Column(Boolean, default=False, nullable=False)

    _constraints = Column("constraints", Text, nullable=True)

    @validates("name")
    def validate_name(self, key, value):
        if not value:
            raise exc.ValidationError("Name is a required field.")

        if not constants.ATTRIBUTE_NAME.match(value):
            raise exc.ValidationError("Invalid name.")

        return value or False

    @validates("display")
    def validate_display(self, key, value):
        if self.required:
            return True
        return value

    @validates("resource_name")
    def validate_resource_name(self, key, value):
        if value not in VALID_ATTRIBUTE_RESOURCES:
            raise exc.ValidationError("Invalid resource name.")
        return value

    @classmethod
    def all_by_name(cls, session, resource_name=None):
        query = session.query(cls)
        if resource_name is not None:
            query = query.filter_by(resource_name=resource_name)

        return {
            attribute.name: attribute
            for attribute in query.all()
        }

    @property
    def constraints(self):
        constraints = {}
        if self._constraints is not None:
            constraints = json.loads(self._constraints)

        return {
            "allow_empty": constraints.get("allow_empty", False),
            "pattern": constraints.get("pattern", ""),
            "valid_values": constraints.get("valid_values", []),
        }

    @constraints.setter
    def constraints(self, value):
        if not isinstance(value, dict):
            raise exc.ValidationError("Expected dictionary but received {}".format(
                type(value)
            ))

        constraints = {
            "allow_empty": value.get("allow_empty", False),
            "pattern": value.get("pattern", ""),
            "valid_values": value.get("valid_values", []),
        }

        if not isinstance(constraints["allow_empty"], bool):
            raise exc.ValidationError("allow_empty expected type bool.")

        if not isinstance(constraints["pattern"], basestring):
            raise exc.ValidationError("pattern expected type string.")

        if not isinstance(constraints["valid_values"], list):
            raise exc.ValidationError("valid_values expected type list")

        self._constraints = json.dumps(constraints)

    def _validate_single_value(self, value, constraints=None):
        if not isinstance(value, basestring):
            raise exc.ValidationError("Attribute values must be a string type")

        if constraints is None:
            constraints = self.constraints

        allow_empty = constraints.get("allow_empty", False)
        if not allow_empty and not value:
            raise exc.ValidationError(
                "Attribute {} doesn't allow empty values".format(self.name)
            )

        pattern = constraints.get("pattern")
        if pattern and not re.match(pattern, value):
            raise exc.ValidationError(
                "Attribute value {} for {} didn't match pattern: {}"
                .format(value, self.name, pattern)
            )

        valid_values = set(constraints.get("valid_values", []))
        if valid_values and value not in valid_values:
            raise exc.ValidationError(
                "Attribute value {} for {} not a valid value: {}"
                .format(value, self.name, ", ".join(valid_values))
            )

        return {
            "attribute_id": self.id,
            "name": self.name,
            "value": value,
        }

    def validate_value(self, value):
        if self.multi:
            if not isinstance(value, list):
                raise exc.ValidationError("Attribute values must be a list type")
        else:
            value = [value]

        inserts = []
        # This does a deserialization so save the result
        constraints = self.constraints
        for val in value:
            inserts.append(self._validate_single_value(val, constraints))

        return inserts

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "description": self.description,
            "name": self.name,
            "resource_name": self.resource_name,
            "required": self.required,
            "display": self.display,
            "multi": self.multi,
            "constraints": self.constraints,
        }


class Change(Model):
    """ Record of all changes in NSoT."""

    __tablename__ = "changes"

    id = Column(Integer, primary_key=True)

    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    site = relationship(Site, lazy="joined", backref=backref("changes", cascade="all,delete-orphan"))

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship(User, lazy="joined", backref="changes")

    change_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    event = Column(String(10), nullable=False)

    resource_name = Column(String(20), nullable=False, index=True)
    resource_id = Column(Integer, nullable=False)

    _resource = Column("resource", Text, nullable=False)

    @validates("event")
    def validate_event(self, key, value):
        if value not in CHANGE_EVENTS:
            raise exc.ValidationError("Invalid Change Event.")
        return value

    @validates("resource_name")
    def validate_resource_name(self, key, value):
        if value not in VALID_CHANGE_RESOURCES:
            raise exc.ValidationError("Invalid resource name.")
        return value

    @property
    def resource(self):
        return json.loads(self._resource)

    @resource.setter
    def resource(self, value):
        self._resource = json.dumps(value)

    @classmethod
    def create(cls, session, user_id, event, resource):

        kwargs = {
            "site_id": resource.site_id,
            "user_id": user_id,
            "event": event,
            "resource_name": resource.model_name,
            "resource_id": resource.id,
            "resource": resource.to_dict(),
        }

        obj = cls(**kwargs).add(session)
        return obj

    def to_dict(self):
        resource = None
        if self.resource is not None:
            resource = self.resource

        return {
            "id": self.id,
            "site": self.site.to_dict(),
            "user": self.user.to_dict(),
            "change_at": timegm(self.change_at.timetuple()),
            "event": self.event,
            "resource_name": self.resource_name,
            "resource_id": self.resource_id,
            "resource": resource,
        }


class Counter(Model):

    __tablename__ = "counters"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=64), unique=True, nullable=False)
    count = Column(Integer, nullable=False, default=0)
    last_modified = Column(DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def incr(cls, session, name, count=1):
        counter = session.query(cls).filter_by(name=name).scalar()
        if counter is None:
            counter = cls(name=name, count=count).add(session)
            session.flush()
            return counter
        counter.count = cls.count + count
        session.flush()
        return counter

    @classmethod
    def decr(cls, session, name, count=1):
        return cls.incr(session, name, -count)
