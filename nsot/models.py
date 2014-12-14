from __future__ import unicode_literals

from datetime import datetime
import functools
import ipaddress
import json
import logging

from sqlalchemy import create_engine, or_, union_all, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, aliased
from sqlalchemy.orm import sessionmaker, Session as _Session
from sqlalchemy.schema import Column, ForeignKey, Index
from sqlalchemy.sql import func, label, literal
from sqlalchemy.types import Integer, String, Text, Boolean, SmallInteger
from sqlalchemy.types import Enum, DateTime, VARBINARY


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


class Site(Model):
    """ A namespace for subnets, ipaddresses, attributes. """

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=32), unique=True, nullable=False)
    description = Column(Text)

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
            "network_broadcast_idx",
            "site_id", "ip_version", "network_address", "broadcast_address",
            unique=True
        ),
    )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)

    ip_version = Column(Enum(4, 6), nullable=False, index=True)

    # Root networks will be NULL while other networks will point to
    # their supernet.
    parent_id = Column(Integer, ForeignKey("networks.id"), nullable=True)

    network_address = Column(VARBINARY(16), nullable=False, index=True)
    broadcast_address = Column(VARBINARY(16), nullable=False, index=True)

    prefix_length = Column(Integer, nullable=False, index=True)

    # Simple boolean
    is_ip = Column(Boolean, nullable=False, default=False, index=True)

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
            "ip_version": network.ip_version,
            "network_address": network.network_address.packed,
            "broadcast_address": network.broadcast_address.packed,
            "prefix_length": network.prefixlen,
            "is_ip": is_ip,
        }

        obj = cls(**kwargs)

        # TODO(gary): Find parent id
        return obj


class Hostname(Model):

    __tablename__ = "hostnames"

    id = Column(Integer, primary_key=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    # Not unique to allow for secondary round-robin names for an IP
    name = Column(String, nullable=False)
    # The primary hostname will be used for reverse DNS. Only one primary
    # hostname is allowed.
    primary = Column(Boolean, nullable=False, index=True)


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
    cascade = Column(Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "site_id": self.site_id,
            "name": self.name,
            "required": self.required,
            "cascade": self.cascade,
        }



class NetworkAttributeValue(Model):

    __tablename__ = "network_attribute_values"

    id = Column(Integer, primary_key=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id"), nullable=False)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)

    value = Column(String, nullable=False)
    # Whether this attribute was explicitly added. This is important
    # if the attribute has been cascaded to an IP
    explicit = Column(Boolean, nullable=False)
