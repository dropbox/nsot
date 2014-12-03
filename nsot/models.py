from datetime import datetime
import functools
import json
import logging

from sqlalchemy import create_engine, or_, union_all, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, object_session, aliased
from sqlalchemy.orm import sessionmaker, Session as _Session
from sqlalchemy.schema import Column, ForeignKey
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

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    ip_version = Column(Enum("4", "6"), nullable=False)

    network_address = Column(VARBINARY(16), nullable=False)
    broadcast_address = Column(VARBINARY(16), nullable=False)

    # If a network, wether an IP Address can be allocated in this subnet
    can_allocate = Column(Boolean, nullable=False)

    # Whether the Network is a single IP address
    is_ipaddress = Column(Boolean, nullable=False)

    prefix_length = Column(Integer, nullable=False)


class Hostname(Model):

    __tablename__ = "hostnames"

    id = Column(Integer, primary_key=True)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)
    name = Column(String, nullable=False)
    # The primary hostname will be used for reverse DNS. Only one primary
    # hostname is allowed.
    primary = Column(Boolean, nullable=False)


class Attribute(Model):

    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)

    required = Column(Boolean, nullable=False)
    cascade = Column(Boolean, nullable=False)

    name = Column(String, nullable=False)


class NetworkAttribute(Model):

    __tablename__ = "network_attributes"

    id = Column(Integer, primary_key=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id"), nullable=False)
    network_id = Column(Integer, ForeignKey("networks.id"), nullable=False)

    value = Column(String, nullable=False)
    # Whether this attribute was explicitly added. This is important
    # if the attribute has been cascaded to an IP
    explicit = Column(Boolean, nullable=False)


class NetworkTree(Model):

    __tablename__ = "network_tree"

    id = Column(Integer, primary_key=True)

    parent_id = Column(Integer, ForeignKey("networks.id"), nullable=True)
    child_id = Column(Integer, ForeignKey("networks.id"), nullable=False)

    distance = Column(SmallInteger)

