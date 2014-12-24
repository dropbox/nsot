from __future__ import unicode_literals

from datetime import datetime
from operator import attrgetter
import functools
import ipaddress
import json
import logging

from sqlalchemy import create_engine, or_, union_all, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, aliased, validates
from sqlalchemy.orm import sessionmaker, Session as _Session
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.sql import func, label, literal
from sqlalchemy.types import Integer, String, Text, Boolean, SmallInteger
from sqlalchemy.types import Enum, DateTime, VARBINARY

from . import exc


class Session(_Session):
    """ Custom session meant to utilize add on the model.

        This Session overrides the add/add_all methods to prevent them
        from being used. This is to for using the add methods on the
        models themselves where overriding is available.
    """

    _add = _Session.add
    _add_all = _Session.add_all

    def add(self, *args, **kwargs):
        raise NotImplementedError("Use add method on models instead.")

    def add_all(self, *args, **kwargs):
        raise NotImplementedError("Use add method on models instead.")


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

    def add(self, session):
        session._add(self)
        return self


Model = declarative_base(cls=Model)


def get_db_engine(url):
    return create_engine(url, pool_recycle=300)


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
    email = Column(String, unique=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    @validates("email")
    def validate_email(self, key, value):
        # TODO(gary): Use a better validator
        if "@" not in value:
            raise exc.ValidationError("Must contain a valid e-mail address")
        return value


class Site(Model):
    """ A namespace for subnets, ipaddresses, attributes. """

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=32), unique=True, nullable=False)
    description = Column(Text)

    @validates("name")
    def validate_email(self, key, value):
        if not value:
            raise exc.ValidationError("Name is a required field.")
        return value

    @classmethod
    def create(cls, session, user_id, **kwargs):
        try:
            site = cls(**kwargs).add(session)
            session.commit()
        except Exception:
            session.rollback()
            raise

        return site

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

        inserts = []
        for name, value in attributes.iteritems():
            if not isinstance(name, basestring):
                raise exc.ValidationError("Attribute names must be a string type")
            if not isinstance(value, basestring):
                raise exc.ValidationError("Attribute values must be a string type")
            if name not in valid_attributes:
                raise exc.ValidationError("Attribute name (%s) invalid." % name)

            attribute_meta = valid_attributes[name]
            inserts.append({
                "network_id": self.id,
                "attribute_id": attribute_meta["id"],
                "name": name,
                "value": value,
            })

        index_table = NetworkAttributeIndex.__table__

        # Always purge the index
        self.session.execute(
            index_table.delete().where(index_table.c.network_id == self.id)
        )

        if inserts:
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

    def subnets(self, session, include_networks=True, include_ips=False, direct=False, for_update=False):
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
        return "{}/{}".format(
            ipaddress.ip_address(self.network_address),
            self.prefix_length
        )

    def __repr__(self):
        return "Network<{}>".format(self.cidr)

    def reparent_subnets(self, session):
        query = session.query(Network).filter(
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
    def create(cls, session, site_id, cidr, attributes=None):
        if attributes is None:
            attributes = {}

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

            obj.reparent_subnets(session)

            session.commit()
        except Exception:
            session.rollback()
            raise

        return obj


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

    name = Column(String, nullable=False)

    required = Column(Boolean, default=False, nullable=False)

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
            "name": self.name,
            "required": self.required,
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

    name = Column(String, nullable=False, index=True)
    value = Column(String, nullable=False, index=True)

    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("network_attributes.id"), nullable=False)


class Counter(Model):

    __tablename__ = "counters"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
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
