# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from nsot import exc, models
from .fixtures import circuit, site


# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db


@pytest.fixture
def asn_attribute(site):
    return models.Attribute.objects.create(
        site=site,
        name='asn',
        resource_name='Protocol',
    )


@pytest.fixture
def bgp(asn_attribute, site):
    bgp = models.ProtocolType.objects.create(
        name='bgp',
        description='Border Gateway Protocol',
        site=site,
    )
    bgp.required_attributes.add(asn_attribute)

    return bgp


@pytest.fixture
def area_attribute(site):
    return models.Attribute.objects.create(
        site=site,
        name='area',
        resource_name='Protocol',
    )


@pytest.fixture
def ospf(area_attribute, site):
    ospf = models.ProtocolType.objects.create(
        name='ospf',
        description='Open Shortest Path First protocol',
        site=site
    )
    ospf.required_attributes.add(area_attribute)

    return ospf


class ProtocolTestCase(object):
    """Shared fixtures for Protocol(Type) tests."""
    @pytest.fixture
    def device(self, circuit):
        return circuit.endpoint_a.device

    @pytest.fixture
    def interface(self, circuit):
        return circuit.endpoint_a


class TestProtocolType(ProtocolTestCase):
    """Test ProtocolType constraints."""
    def test_required_attributes_site(self, site, bgp, area_attribute):
        """Test that required_attributes are in same site."""
        # Create a 2nd site and 2 protocol attributes.
        site2 = models.Site.objects.create(name='Site2')
        attr1 = models.Attribute.objects.create(
            resource_name='Protocol', name='attr1', site=site2
        )
        attr2 = models.Attribute.objects.create(
            resource_name='Protocol', name='attr2', site=site2
        )

        # Adding attributes from wrong site should fail.
        with pytest.raises(exc.ValidationError):
            bgp.required_attributes.add(attr1, attr2)

    def test_required_attributes_resource(self, site, bgp):
        """Test Protocol attributes only for required_attributes."""
        bad_attr = models.Attribute.objects.create(
            site=site, name='bad', resource_name='Device'
        )

        # Adding attributes from wrong resource should fail.
        with pytest.raises(exc.ValidationError):
            bgp.required_attributes.add(bad_attr)


class TestCreation(ProtocolTestCase):
    def test_normal_conditions(self, device, circuit, bgp):
        """
        Under normal conditions, ensure that a Protocol can be created without
        raising any exceptions
        """
        protocol = models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type=bgp,
            description='My fancy peer',
            attributes={
                'asn': '1234',
            }
        )
        protocol.save()

        assert protocol.site_id == device.site_id
        assert protocol in device.protocols.all()
        assert protocol in circuit.protocols.all()

    def test_bad_circuit(self, device, circuit, bgp):
        """
        Ensure a ValidationError is thrown when we try to create a Protocol
        where the Circuit is not attached to the Device
        """
        bad_circuit = circuit
        bad_circuit.endpoint_a = bad_circuit.endpoint_z

        with pytest.raises(exc.ValidationError):
            models.Protocol.objects.create(
                device=device,
                circuit=bad_circuit,
                type=bgp,
                attributes={
                    'asn': '1234',
                }
            )

    def test_attributes(self, device, circuit, bgp):
        """ Ensure that we can set arbitrary attributes on a Protocol """
        models.Attribute.objects.create(
            site=device.site, resource_name='Protocol', name='import_policies')

        protocol = models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type=bgp,
            attributes={
                'asn': '1234',
                'import_policies': 'foo'
            }
        )

        assert protocol.get_attributes()['import_policies'] == 'foo'

    def test_missing_attributes(self, device, circuit, bgp):
        """
        Test that a ValidationError is thrown when we try to create a Protocol.
        The BGP ProtocolType we defined has a required attribute `asn`
        """
        with pytest.raises(exc.ValidationError):
            models.Protocol.objects.create(
                device=device,
                circuit=circuit,
                type=bgp,
                attributes={},
            )

    def test_another_protocol(self, device, interface, ospf):
        """
        Test that we can add a Protocol with second ProtocolType and that it
        doesn't raise any sort of exception
        """
        models.Protocol.objects.create(
            device=device,
            interface=interface,
            type=ospf,
            attributes={'area': 'threeve'}
        )

    def test_mixed_attrs(self, device, circuit, bgp, area_attribute):
        """
        Test that we can add a Protocol of one ProtocolType with an attribute
        that's required by another ProtocolType without anything weird
        happening
        """
        protocol = models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type=bgp,
            attributes={
                'asn': '1234',
                'area': 'threeve',
            }
        )

        assert protocol.get_attributes()['asn'] == '1234'
        assert protocol.get_attributes()['area'] == 'threeve'


class TestUnicode(ProtocolTestCase):
    """
    Tests for the __unicode__ method on Protocol
    """
    @pytest.fixture
    def base_protocol(self, bgp, circuit):
        device = circuit.endpoint_a.device

        return models.Protocol.objects.create(
            device=device,
            type=bgp,
            attributes={
                'asn': '1234',
            }
        )

    def test_circuit(self, base_protocol, circuit):
        """
        Case when only a circuit is set on the Protocol (no interface)
        """
        expected = 'bgp over foo-bar1:eth0_foo-bar2:eth0'

        base_protocol.circuit = circuit
        base_protocol.save()

        assert base_protocol.circuit is not None
        assert base_protocol.interface is None

        assert unicode(base_protocol) == expected

    def test_interface(self, base_protocol, interface):
        """
        Case when only an interface is set on the Protocol (no circuit)
        """
        expected = 'bgp on foo-bar1:eth0'

        base_protocol.interface = interface
        base_protocol.save()

        assert base_protocol.interface is not None
        assert base_protocol.circuit is None

        assert unicode(base_protocol) == expected

    def test_neither_circuit_nor_interface(self, base_protocol):
        """
        Case when neither a circuit nor interface are set
        """
        expected = 'bgp on foo-bar1'

        assert base_protocol.circuit is None
        assert base_protocol.interface is None

        assert unicode(base_protocol) == expected

    def test_both_circuit_and_interface(self, base_protocol, circuit,
                                        interface):
        """
        Case when both a circuit and interface are set
        """
        expected = 'bgp over foo-bar1:eth0_foo-bar2:eth0'

        base_protocol.circuit = circuit
        base_protocol.interface = interface
        base_protocol.save()

        assert base_protocol.circuit is not None
        assert base_protocol.interface is not None

        assert unicode(base_protocol) == expected
