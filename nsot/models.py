from __future__ import unicode_literals

from calendar import timegm
from datetime import datetime
from email.utils import parseaddr
from operator import attrgetter
import functools
import ipaddress
import json
import logging
import time

from sqlalchemy import create_engine, or_, union_all, desc
from sqlalchemy.event import listen
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, aliased, validates
from sqlalchemy.orm import synonym, sessionmaker, Session as _Session, backref
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.sql import func, label, literal
from sqlalchemy.types import Integer, String, Text, Boolean, SmallInteger
from sqlalchemy.types import Enum, DateTime, VARBINARY

from . import constants
from . import exc
from .permissions import PermissionsFlag


RESOURCE_BY_IDX = (
    "Site", "Network", "NetworkAttribute", "Permission",
)
RESOURCE_BY_NAME = {
    obj_type: idx
    for idx, obj_type in enumerate(RESOURCE_BY_IDX)
}
CHANGE_EVENTS = ("Create", "Update", "Delete")


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

    @property
    def session(self):
        return object_session(self)

    @classmethod
    def get_or_create(cls, session, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).scalar()
        if instance:
            return instance, False

        instance = cls(**kwargs)
        instance.add(session)

        return instance, True

    @property
    def resource_type(self):
        obj_name = type(self).__name__
        obj_idx = RESOURCE_BY_NAME.get(obj_name)
        if obj_idx is None:
            raise NotImplementedError()
        return obj_idx

    @classmethod
    def before_create(cls, session, user_id):
        """ Hook for before object creation."""

    def after_create(self, user_id):
        """ Hook for after object creation."""

    @classmethod
    def create(cls, session, _user_id, **kwargs):
        try:
            cls.before_create(session, _user_id)
            obj = cls(**kwargs).add(session)
            session.flush()
            obj.after_create(_user_id)
            Change.create(session, _user_id, "Create", obj)
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


def get_db_engine(url):
    engine = create_engine(url, pool_recycle=300)
    if engine.driver == "pysqlite":
        listen(engine, "connect", _set_sqlite_pragma)

    return engine


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
            logging.exception("Transaction Failed. Rolling back.")
            if self.session is not None:
                self.session.rollback()
            raise
        return ret
    return wrapper


class User(Model):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(length=255), unique=True, nullable=False)

    @validates("email")
    def validate_email(self, key, value):
        _, email = parseaddr(value)
        if email == '' or "@" not in value:
            raise exc.ValidationError("Must contain a valid e-mail address")
        return value

    def to_dict(self, with_permissions=False):
        out = {
            "id": self.id,
            "email": self.email,
        }
        if with_permissions:
            out["permissions"] = self.get_permissions()

        return out

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

    def networks(self, include_networks=True, include_ips=False, root=False,
                 attribute_name=None, attribute_value=None):
        """ Helper method for grabbing Networks.

            Args:
                include_networks: Whether the response should include non-ip
                                  address networks
                include_ips: Whether the response should include ip addresses
                root: Only return networks at the root.
                attribute_name: Filter to networks that contain this attribute name
                attribute_value: Filter to networks that contain this attribute value
        """

        if not any([include_networks, include_ips]):
            return []

        if attribute_value is not None and attribute_name is None:
            raise ValueError("attribute_value requires attribute_name to be set.")

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

        networks = query.all()
        return networks


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


class Network(Model):
    """ Represents a subnet or ipaddress. """

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

    ip_version = Column(Enum("4", "6"), nullable=False, index=True)

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

    # Attributes is a Serialized LOB field. Lookups of these attributes
    # is done against an Inverted Index table
    _attributes = Column("attributes", Text)

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

    def _purge_attribute_index(self):
        index_table = NetworkAttributeIndex.__table__

        # Always purge the index
        self.session.execute(
            index_table.delete().where(index_table.c.network_id == self.id)
        )

    def before_delete(self):
        self._purge_attribute_index()

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
            valid_attributes = NetworkAttribute.all_by_name(self.session)

        missing_attributes = {
            value["name"]
            for value in valid_attributes.itervalues()
            if value["required"] and value["name"] not in attributes
        }

        if missing_attributes:
            raise exc.ValidationError("Missing required attributes: {}".format(
                ", ".join(missing_attributes)
            ))

        inserts = []
        for name, value in attributes.iteritems():
            if not isinstance(name, basestring):
                raise exc.ValidationError("Attribute names must be a string type")
            if not isinstance(value, basestring):
                raise exc.ValidationError("Attribute values must be a string type")
            if name not in valid_attributes:
                raise exc.ValidationError("Attribute name (%s) does not exist.".format(
                    name
                ))

            attribute_meta = valid_attributes[name]
            inserts.append({
                "network_id": self.id,
                "attribute_id": attribute_meta["id"],
                "name": name,
                "value": value,
            })


        self._purge_attribute_index()
        if inserts:
            index_table = NetworkAttributeIndex.__table__
            self.session.execute(index_table.insert(), inserts)

        self._attributes = json.dumps(attributes)

    def supernets(self, session, direct=False, discover_mode=False, for_update=False):
        """ Get networks that are a supernet of a network.

            Args:
                direct: Only return direct supernet.
                discover_mode: Prevent new networks from bailing for missing parent_id
                for_update: Lock these rows because they're selected for updating.

        """

        if self.parent_id is None and not discover_mode:
            return []

        if discover_mode and direct:
            raise ValueError("direct is incompatible with discover_mode")

        query = session.query(Network)
        if for_update:
            query = query.with_for_update()

        if direct:
            return query.filter(Network.id == self.parent_id).all()

        return query.filter(
            Network.is_ip == False,
            Network.ip_version == self.ip_version,
            Network.prefix_length < self.prefix_length,
            Network.network_address <= self.network_address,
            Network.broadcast_address >= self.broadcast_address
        ).all()

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
            return []

        query = session.query(Network)
        if for_update:
            query = query.with_for_update()

        if not all([include_networks, include_ips]):
            if include_networks:
                query = query.filter(Network.is_ip == False)
            if include_ips:
                query = query.filter(Network.is_ip == True)

        if direct:
            return query.filter(Network.parent_id == self.id).all()

        return query.filter(
            Network.ip_version == self.ip_version,
            Network.prefix_length > self.prefix_length,
            Network.network_address >= self.network_address,
            Network.broadcast_address <= self.broadcast_address
        ).all()

    @property
    def cidr(self):
        return u"{}/{}".format(
            ipaddress.ip_address(self.network_address).exploded,
            self.prefix_length
        )

    def __repr__(self):
        return "Network<{}>".format(self.cidr)

    def reparent_subnets(self, session):
        query = session.query(Network).with_for_update().filter(
            Network.parent_id == self.parent_id,
            Network.id != self.id  # Don't include yourself...
        )

        # When adding a new root we're going to reparenting a subset
        # of roots so it's a bit more complicated so limit to all subnetworks
        if self.parent_id is None:
            query = query.filter(
                Network.is_ip == False,
                Network.ip_version == self.ip_version,
                Network.prefix_length > self.prefix_length,
                Network.network_address >= self.network_address,
                Network.broadcast_address <= self.broadcast_address
            )

        query.update({Network.parent_id: self.id})

    @classmethod
    def create(cls, session, user_id, site_id, cidr, attributes=None):
        if attributes is None:
            attributes = {}

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

            supernets = obj.supernets(session, discover_mode=True, for_update=True)
            if supernets:
                parent = max(supernets, key=attrgetter("prefix_length"))
                obj.parent_id = parent.id


            if obj.parent_id is None and is_ip:
                raise exc.ValidationError("IP Address needs base network.")

            if not is_ip:
                obj.reparent_subnets(session)

            session.flush()
            Change.create(session, user_id, "Create", obj)

            session.commit()
        except Exception:
            session.rollback()
            raise

        return obj

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


class NetworkAttribute(Model):

    __tablename__ = "network_attributes"
    __table_args__ = (
        Index(
            "name_idx",
            "site_id", "name",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)

    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    # This is purposely not unique as there is a compound index with site_id.
    name = Column(String(length=64), nullable=False)
    description = Column(Text, default="", nullable=False)
    required = Column(Boolean, default=False, nullable=False)

    @validates("name")
    def validate_name(self, key, value):
        if not value:
            raise exc.ValidationError("Name is a required field.")

        if not constants.ATTRIBUTE_NAME.match(value):
            raise exc.ValidationError("Invalid name.")

        return value


    @classmethod
    def all_by_name(cls, session):
        return {
            attribute.name: attribute.to_dict()
            for attribute in session.query(cls).all()
        }

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "description": self.description,
            "name": self.name,
            "required": self.required,
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

    event = Column(Enum(*CHANGE_EVENTS), nullable=False)

    resource_type = Column(Integer, nullable=False)
    resource_id = Column(Integer, nullable=False)

    _resource = Column("resource", Text, nullable=False)

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
            "resource_type": resource.resource_type,
            "resource_id": resource.id,
            "resource": resource.to_dict(),
        }

        obj = cls(**kwargs).add(session)
        session.flush()

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
            "resource_type": RESOURCE_BY_IDX[self.resource_type],
            "resource_id": self.resource_id,
            "resource": resource,
        }


class NetworkAttributeIndex(Model):
    """ An Inverted Index for looking up Networks by their attributes."""

    __tablename__ = "network_attribute_index"
    __table_args__ = (
        # Ensure that each network can only have one of each attribute
        Index(
            "single_attr_idx",
            "network_id", "attribute_id",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)

    name = Column(String(length=64), nullable=False, index=True)
    value = Column(String(length=255), nullable=False, index=True)

    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    network = relationship(Network, backref="attr_idx")

    attribute_id = Column(Integer, ForeignKey("network_attributes.id"), nullable=False)
    attribute = relationship(NetworkAttribute)


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
