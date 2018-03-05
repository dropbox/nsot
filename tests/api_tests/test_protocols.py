# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db

import copy
from django.core.urlresolvers import reverse
import json
import logging
from rest_framework import status

from .fixtures import live_server, client, user, site, user_client
from .util import (
    assert_created, assert_error, assert_success, assert_deleted, load_json,
    Client, SiteHelper, load, filter_circuits, get_result
)


log = logging.getLogger(__name__)


@pytest.fixture
def asn_attribute(site, client):
    """``Protocol:asn`` attribute."""
    attr_uri = site.list_uri('attribute')
    resp = client.create(attr_uri, name='asn', resource_name='Protocol')
    return resp.json()


@pytest.fixture
def metric_attribute(site, client):
    """``Protocol:metric`` attribute."""
    attr_uri = site.list_uri('attribute')
    resp = client.create(attr_uri, name='metric', resource_name='Protocol')
    return resp.json()


@pytest.fixture
def bgp_type(site, client, asn_attribute):
    """ProtocolType instance of 'bgp' with 'asn' as required attribute."""
    pt_uri = site.list_uri('protocoltype')
    resp = client.create(pt_uri, name='bgp', required_attributes=['asn'])
    return resp.json()


@pytest.fixture
def isis_type(site, client, metric_attribute):
    """ProtocolType instance of 'isis' with 'metric' as required attribute."""
    pt_uri = site.list_uri('protocoltype')
    resp = client.create(pt_uri, name='isis', required_attributes=['metric'])
    return resp.json()


class TestProtocolType(object):
    """Tests for ProtocolType resource object."""

    def test_name_uniqueness(self, site, client, bgp_type):
        """Test that site/name uniqueness is enforced."""
        pt_uri = site.list_uri('protocoltype')

        # BGP already exists in this site.
        assert_error(
            client.create(pt_uri, name='bgp'),
            status.HTTP_400_BAD_REQUEST
        )

    def test_lookup_by_natural_key(self, site, client, bgp_type):
        """Test that ProtocolType can be looked up by natural key."""
        natural_uri = site.detail_uri('protocoltype', id='bgp')
        assert_success(client.retrieve(natural_uri), bgp_type)

    def test_required_attributes_site(self, site, client, bgp_type):
        """Test required_attributes are in same site."""
        site_uri = reverse('site-list')
        site_resp = client.create(site_uri, name='Other Site')
        site2 = SiteHelper(site_resp.json())

        # Create site2 attribute/protocoltype
        attr_uri = site2.list_uri('attribute')
        pt_uri = site2.list_uri('protocoltype')

        # Attribute
        attr_resp = client.create(attr_uri, name='bad', resource_name='Device')
        attr = attr_resp.json()

        # ProtocolType
        pt_resp = client.create(pt_uri, name='bgp2')
        pt = pt_resp.json()
        pt_obj_uri = site2.detail_uri('protocoltype', id=pt['id'])

        # Should fail.
        pt['required_attributes'] = [attr['id']]
        assert_error(
            client.update(pt_obj_uri, **pt),
            status.HTTP_400_BAD_REQUEST
        )

    def test_required_attributes_resource(self, site, client, bgp_type,
                                          asn_attribute):
        """Test Protocol attributes only for required_attributes."""
        attr_uri = site.list_uri('attribute')
        pt_uri = site.list_uri('protocoltype')

        r = client.create(attr_uri, name='bad', resource_name='Device')
        attr = r.json()
        bad_attributes = [attr['id']]

        pt_resp = client.create(pt_uri, name='bgp2')
        pt = pt_resp.json()
        pt_obj_uri = site.detail_uri('protocoltype', id=pt['id'])

        # Set bad required_attributes. Should fail.
        pt['required_attributes'] = bad_attributes
        assert_error(
            client.update(pt_obj_uri, **pt),
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_required_attributes(self, site, client, bgp_type,
                                        asn_attribute):
        """Test update of required_attributes by id or natural key."""
        pt_obj_uri = site.detail_uri('protocoltype', id=bgp_type['id'])
        attrs_by_id = [asn_attribute['id']]
        attrs_by_name = [asn_attribute['name']]

        payload = copy.deepcopy(bgp_type)
        expected = copy.deepcopy(bgp_type)

        # Set required_attributes by id. Should succeed.
        payload['required_attributes'] = attrs_by_id
        expected['required_attributes'] = attrs_by_name
        assert_success(client.update(pt_obj_uri, **payload), expected)

        # Set required_attributes by name. Should succeed.
        payload['required_attributes'] = attrs_by_name
        assert_success(client.update(pt_obj_uri, **payload), expected)

        # Set bogus required_attributes. Should fail.
        payload['required_attributes'] = ['bogus']
        assert_error(
            client.update(pt_obj_uri, **payload),
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_by_natural_key(self, site, client, bgp_type):
        """Test updated of ProtocolType using natural key."""
        natural_uri = site.detail_uri('protocoltype', id=bgp_type['name'])
        bgp_type['required_attributes'] = []
        assert_success(client.update(natural_uri, **bgp_type), bgp_type)

    def test_partial_update(self, site, client, bgp_type):
        """Test partial update of ProtocolType."""
        obj_uri = site.detail_uri('protocoltype', id=bgp_type['id'])

        # Partial update to name
        bgp_type['name'] = 'patched'
        assert_success(
            client.partial_update(obj_uri, name='patched'),
            bgp_type
        )

        # Partial update to description
        bgp_type['description'] = 'also patched'
        assert_success(
            client.partial_update(obj_uri, description='also patched'),
            bgp_type
        )

    def test_delete_by_id(self, site, client, bgp_type):
        """Test delete by primary key."""
        id_uri = site.detail_uri('protocoltype', id=bgp_type['id'])
        assert_deleted(client.delete(id_uri))

    def test_delete_by_natural_key(self, site, client, bgp_type):
        """Test delete by natural key."""
        natural_uri = site.detail_uri('protocoltype', id=bgp_type['name'])
        assert_deleted(client.delete(natural_uri))

    def test_filtering(self, site, client, bgp_type):
        """Test query parameter filtering."""
        pt_uri = site.list_uri('protocoltype')
        bgp2_resp = client.create(pt_uri, name='bgp2', description='bgp2')
        bgp2_type = get_result(bgp2_resp)

        # Filter by name
        assert_success(client.retrieve(pt_uri, name='bgp'), [bgp_type])

        # Filter by description
        assert_success(client.retrieve(pt_uri, description='bgp2'), [bgp2_type])


class ProtocolTestCase(object):
    """Reusable test class for Protocol objects with common fixtures."""

    @pytest.fixture
    def device(self, site, client):
        """foo-bar1"""
        dev_uri = site.list_uri('device')
        r = client.create(dev_uri, hostname='foo-bar1')
        dev = get_result(r)
        return dev

    @pytest.fixture
    def device2(self, site, client):
        """spam-bar2"""
        dev_uri = site.list_uri('device')
        r = client.create(dev_uri, hostname='spam-bar2')
        dev = get_result(r)
        return dev

    @pytest.fixture
    def interface(self, site, client, device):
        """foo-bar1:eth0"""
        ifc_uri = site.list_uri('interface')
        r = client.create(ifc_uri, device=device['id'], name='eth0')
        ifc = get_result(r)
        return ifc

    @pytest.fixture
    def circuit(self, site, client, device, interface):
        cir_uri = site.list_uri('circuit')
        dev_uri = site.list_uri('device')
        ifc_uri = site.list_uri('interface')
        net_uri = site.list_uri('network')

        # Devices
        dev_a = device
        dev_z_resp = client.create(dev_uri, hostname='foo-bar2')
        dev_z = get_result(dev_z_resp)

        # Parent network for interface assignments
        net_resp = client.create(net_uri, cidr='10.32.0.0/24')
        net = get_result(net_resp)

        # Interfaces
        if_a = interface
        if_z_resp = client.create(
          ifc_uri, device=dev_z['id'], name='eth0', addresses=['10.32.0.2/32']
        )
        if_z = get_result(if_z_resp)

        cir_resp = client.create(
          cir_uri, endpoint_a=if_a['id'], endpoint_z=if_z['id']
        )
        cir = get_result(cir_resp)

        return cir

    @pytest.fixture
    def bgp_protocol(self, site, client, device, bgp_type, circuit):
        """Protocol w/ circuit."""
        proto_uri = site.list_uri('protocol')
        proto_resp = client.create(
            proto_uri, device=device['hostname'], type=bgp_type['name'],
            attributes={'asn': '12345'}, circuit=circuit['name_slug'],
            description='Border Gateway Protocol'
        )
        proto = get_result(proto_resp)
        return proto

    @pytest.fixture
    def isis_protocol(self, site, client, device, isis_type, interface):
        """Protocol w/ interface."""
        proto_uri = site.list_uri('protocol')
        proto_resp = client.create(
            proto_uri, device=device['hostname'], type=isis_type['name'],
            attributes={'metric': '100'}, interface=interface['name_slug'],
            description='IS-IS'
        )
        proto = get_result(proto_resp)
        return proto


class TestCreation(ProtocolTestCase):
    def test_basic(self, site, client, device, bgp_type):
        """Test basic creation of a Protocol."""
        proto_uri = site.list_uri('protocol')

        # - Device referenced by natural key
        # - Type referenced by natural key
        proto_resp = client.create(
            proto_uri, device=device['hostname'], type=bgp_type['name'],
            attributes={'asn': '12345'}
        )
        proto = get_result(proto_resp)
        proto_obj_uri = site.detail_uri('protocol', id=proto['id'])

        # Valid creation
        assert_created(proto_resp, proto_obj_uri)

        # Missing required attributes (per .type). Will fail.
        assert_error(
            client.create(
                proto_uri, device=device['hostname'], type=bgp_type['name']
            ),
            status.HTTP_400_BAD_REQUEST
        )

    def test_with_interface(self, site, client, device, interface, bgp_type):
        """Test creation of a Protocol with a bound Interface."""
        proto_uri = site.list_uri('protocol')

        # - Device referenced by natural key
        # - Type referenced by natural key
        # - Interface referenced by natural key
        proto_resp = client.create(
            proto_uri, device=device['hostname'], type=bgp_type['name'],
            interface=interface['name_slug'], attributes={'asn': '12345'}
        )
        proto = get_result(proto_resp)
        proto_obj_uri = site.detail_uri('protocol', id=proto['id'])

        assert_created(proto_resp, proto_obj_uri)

    def test_with_circuit(self, site, client, device, circuit, bgp_type):
        """Test creation of a Protocol with a bound Interface."""
        proto_uri = site.list_uri('protocol')

        # - Device referenced by natural key
        # - Type referenced by natural key
        # - Circuit referenced by natural key
        proto_resp = client.create(
            proto_uri, device=device['hostname'], type=bgp_type['name'],
            circuit=circuit['name_slug'], attributes={'asn': '12345'}
        )
        proto = get_result(proto_resp)
        proto_obj_uri = site.detail_uri('protocol', id=proto['id'])

        assert_created(proto_resp, proto_obj_uri)


class TestRetrieval(ProtocolTestCase):
    def test_lookup_by_id(self, site, client, bgp_protocol):
        """Test basic lookup by primary key."""
        obj_uri = site.detail_uri('protocol', id=bgp_protocol['id'])
        assert_success(client.retrieve(obj_uri), bgp_protocol)

    def test_filters_by_id(self, site, client, device, interface,
                           circuit, bgp_type, bgp_protocol, isis_protocol):
        """Test filtering by primary key (id)."""
        proto_uri = site.list_uri('protocol')

        # Filter by description
        expected = [isis_protocol]
        assert_success(
            client.retrieve(proto_uri, description='IS-IS'),
            expected
        )

        # Filter by type
        expected = [bgp_protocol]
        assert_success(
            client.retrieve(proto_uri, type=bgp_type['id']),
            expected
        )

        # Filter by device
        expected = [bgp_protocol, isis_protocol]
        assert_success(
            client.retrieve(proto_uri, device=device['id']),
            expected
        )

        # Filter by circuit
        expected = [bgp_protocol]
        assert_success(
            client.retrieve(proto_uri, circuit=circuit['id']),
            expected
        )

        # Filter by interface
        expected = [isis_protocol]
        assert_success(
            client.retrieve(proto_uri, interface=interface['id']),
            expected
        )

    def test_filters_by_natural_key(self, site, client, device, interface,
                                    circuit, bgp_protocol, isis_protocol):
        """Test filtering by natural key."""
        proto_uri = site.list_uri('protocol')

        # Filter by description
        expected = [isis_protocol]
        assert_success(
            client.retrieve(proto_uri, description='IS-IS'),
            expected
        )

        # Filter by type
        expected = [bgp_protocol]
        assert_success(client.retrieve(proto_uri, type='bgp'), expected)

        # Filter by device
        expected = [bgp_protocol, isis_protocol]
        assert_success(
            client.retrieve(proto_uri, device=device['hostname']),
            expected
        )

        # Filter by circuit
        expected = [bgp_protocol]
        assert_success(
            client.retrieve(proto_uri, circuit=circuit['name_slug']),
            expected
        )

        # Filter by interface
        expected = [isis_protocol]
        assert_success(
            client.retrieve(proto_uri, interface=interface['name_slug']),
            expected
        )

    def test_set_queries(self, site, client, bgp_protocol, isis_protocol):
        """Test set query operations."""
        proto_uri = site.list_uri('protocol')
        query_uri = site.query_uri('protocol')
        attr_uri = site.list_uri('attribute')

        bgp = bgp_protocol
        isis = isis_protocol

        bgp_uri = site.detail_uri('protocol', id=bgp['id'])
        isis_uri = site.detail_uri('protocol', id=isis['id'])

        bgp['attributes'].update({'admin_status': 'down', 'peer_as': '19679'})
        isis['attributes'].update({'admin_status': 'up', 'peer_as': '19679'})

        # Pre-load the Attributes
        client.post(attr_uri, data=load('attributes.json'))

        # Update the Protocol objects w/ thew new attributes
        client.update(bgp_uri, **bgp)
        client.update(isis_uri, **isis)

        # Set queries
        # INTERSECTION: peer_as=19679
        expected = [bgp, isis]
        assert_success(
            client.retrieve(query_uri, query='peer_as=19679'),
            expected
        )

        # INTERSECTION: peer_as=19679 asn=12345
        expected = [bgp]
        assert_success(
            client.retrieve(query_uri, query='peer_as=19679 asn=12345'),
            expected
        )

        # DIFFERENCE: -asn=12345
        expected = [isis]
        assert_success(
            client.retrieve(query_uri, query='-asn=12345'),
            expected
        )

        # UNION: asn=12345 +metric=100
        expected = [bgp, isis]
        assert_success(
            client.retrieve(query_uri, query='asn=12345 +metric=100'),
            expected
        )

        # UNIQUE: peer_as=19679 admin_status=up
        expected = [isis]
        assert_success(
            client.retrieve(
                query_uri, query='peer_as=19679 admin_status=up', unique=True
            ),
            expected
        )

        # ERROR: not unique (peer_as=19679)
        assert_error(
            client.retrieve(query_uri, query='peer_as=19679', unique=True),
            status.HTTP_400_BAD_REQUEST
        )

        # ERROR: no result (vendor=bogus)
        assert_error(
            client.retrieve(query_uri, query='peer_as=tacos', unique=True),
            status.HTTP_400_BAD_REQUEST
        )

        # ERROR: bad query
        assert_error(
            client.retrieve(query_uri, query='bacon=delicious'),
            status.HTTP_400_BAD_REQUEST
        )


class TestUpdate(ProtocolTestCase):
    """Test update on Protocol objects."""
    def test_update_by_id(self, site, client, bgp_protocol, device):
        obj_uri = site.detail_uri('protocol', id=bgp_protocol['id'])
        expected = copy.deepcopy(bgp_protocol)
        bgp_protocol['device'] = device['id']
        assert_success(client.update(obj_uri, **bgp_protocol), expected)

    def test_update_related_natural_key(self, site, client, bgp_protocol,
                                        isis_protocol, isis_type, device,
                                        device2, interface):
        """Test update of related fields using natural keys."""
        obj_uri = site.detail_uri('protocol', id=bgp_protocol['id'])

        expected = copy.deepcopy(bgp_protocol)

        # Update type
        expected['type'] = isis_type['name']
        expected['attributes'].update({'metric': '100'})
        assert_success(client.update(obj_uri, **expected), expected)

        # Update device
        circuit_name = expected['circuit']
        expected['type'] = 'bgp'
        expected['device'] = device2['hostname']
        expected['circuit'] = None
        assert_success(client.update(obj_uri, **expected), expected)

        # Interface (Flip interface w/ circuit)
        expected['device'] = device['hostname']
        expected['circuit'] = None
        expected['interface'] = interface['name_slug']
        assert_success(client.update(obj_uri, **expected), expected)

        # Circuit (Flip interface w/ circuit)
        expected['circuit'] = circuit_name
        expected['interface'] = None
        assert_success(client.update(obj_uri, **expected), expected)

    def test_partial_update(self, site, client, bgp_protocol,
                                        isis_protocol, isis_type, device,
                                        device2, interface):
        """Test partial update for each field."""
        obj_uri = site.detail_uri('protocol', id=bgp_protocol['id'])

        expected = copy.deepcopy(bgp_protocol)

        # description
        payload = {'description': 'patched'}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # auth_string
        payload = {'auth_string': 'abc123'}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # device
        payload = {'device': device['hostname']}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # circuit
        payload = {'circuit': None}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # interface
        payload = {'interface': None}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # type
        payload = {'type': isis_type['name'], 'attributes': {'metric': '100'}}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)

        # attributes
        payload = {'attributes': {'metric': '200'}}
        expected.update(payload)
        assert_success(client.partial_update(obj_uri, **payload), expected)


class TestDeletion(ProtocolTestCase):
    """Test delete on Protocol objects."""
    def test_delete_by_id(self, site, client, bgp_protocol):
        """Test simple delete by primary key."""
        obj_uri = site.detail_uri('protocol', id=bgp_protocol['id'])
        assert_deleted(client.delete(obj_uri))
