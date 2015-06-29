"""
Make dummy data and fixtures and stuff to use in benchmarking.
"""

import collections
import faker
import json
import hashlib
from hashlib import sha1
import ipaddress
import pytest
import random
import socket
import struct
import time


# Constants and stuff
fake = faker.Factory.create()

# Phony attributes to randomly generate for testing.
ATTRIBUTE_DATA = {
    'lifecycle': ['monitored', 'ignored'],
    'owner': ['jathan', 'gary', 'lisa', 'jimmy', 'bart', 'bob', 'alice'],
    'metro': ['lax', 'iad', 'sjc', 'tyo'],
    'foo': ['bar', 'baz', 'spam'],
}

# Used to store Attribute/value pairs
Attribute = collections.namedtuple('Attribute', 'name value')


def rando():
    return random.choice((True, False))


def generate_words(num_items=100, title=False, add_suffix=False):
    stuff = set()
    for _ in range(num_items + 1):
        things = (fake.word(), fake.first_name(), fake.last_name())
        suffix = str(random.randint(1, 32)) if add_suffix else ''
        word = random.choice(things) + suffix

        # Title it?
        if rando():
            word = word.title()

        # Reverse it?
        if rando():
            word = word[::-1]  # Reverse it

        # Lower it?
        else:
            word = word.lower()

        # stuff.add(word)
        yield word


def generate_hostnames(num_items=100):
    """
    Generate a random list of hostnames.

    :param num_items:
        Number of items to generate
    """

    for i in range(1, num_items + 1):
        yield 'host%s' % i


def generate_ipv4():
    """Generate a random IPv4 address."""
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))


def generate_ipv4list(num_items=100, include_hosts=False):
    """
    Generate a list of unique IPv4 addresses. This is a total hack.

    :param num_items:
        Number of items to generate

    :param include_hosts:
        Whether to include /32 addresses
    """
    ipset = set()
    # Keep iterating and hack together cidr prefixes if we detect empty
    # trailing octects. This is so lame that we'll mostly just end up with a
    # bunch of /24 networks.
    while len(ipset) < num_items:
        ip = generate_ipv4()
        if ip.startswith('0'):
            continue

        if ip.endswith('.0.0.0'):
            prefix = '/8'
        elif ip.endswith('.0.0'):
            prefix = '/16'
        elif ip.endswith('.0'):
            prefix = '/24'
        elif include_hosts:
            prefix = '/32'
        else:
            continue

        ip += prefix
        ipset.add(ip)
    return sorted(ipset)


def enumerate_attributes(resource_name, attributes=None):
    if attributes is None:
        attributes = ATTRIBUTE_DATA

    for name in attributes:
        yield {'name': name, 'resource_name': resource_name}


def generate_attributes(attributes=None, as_dict=True):
    """
    Randomly choose attributes and values for testing.

    :param attributes:
        Dictionary of attribute names and values

    :param as_dict:
        If set return a dict vs. list of Attribute objects
    """
    if attributes is None:
        attributes = ATTRIBUTE_DATA
    attrs = []
    for attr_name, attr_values in attributes.iteritems():
        if random.choice((True, False)):
            attr_value = random.choice(attr_values)
            attrs.append(Attribute(attr_name, attr_value))
    if as_dict:
        attrs = dict(attrs)
    return attrs


def generate_devices(num_items=100, with_attributes=True):
    """
    Return a list of dicts for Device creation.

    :param num_items:
        Number of items to generate

    :param with_attributes:
        Whether to include Attributes
    """
    hostnames = generate_hostnames(num_items)

    devices = []
    for hostname in hostnames:
        item = {'hostname': hostname}
        if with_attributes:
            attributes = generate_attributes()
            item['attributes'] = attributes

        yield item
        # devices.append(item)
    # return devices


def generate_networks(num_items=100, with_attributes=True, include_hosts=False):
    """
    Return a list of dicts for Network creation.

    :param num_items:
        Number of items to generate

    :param with_attributes:
        Whether to include Attributes
    """
    ipv4list = generate_ipv4list(num_items, include_hosts=include_hosts)

    networks = []
    for cidr in ipv4list:
        attributes = generate_attributes()
        item = {'cidr': cidr}
        if with_attributes:
            attributes = generate_attributes()
            item['attributes'] = attributes

        networks.append(item)
    return networks


def rando_set_action():
    return random.choice(['+', '-', ''])


def rando_set_query():
    action = rando_set_action()
    return ' '.join(
        action + '%s=%s' % (k, v) for k,v in generate_attributes().iteritems()
    )
