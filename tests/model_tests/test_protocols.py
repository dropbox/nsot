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
def bgp(asn_attribute):
    bgp = models.ProtocolType.objects.create(
        name='bgp',
        description='Border Gateway Protocol',
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
def ospf(area_attribute):
    ospf = models.ProtocolType.objects.create(
        name='ospf',
        description='Open Shortest Path First protocol',
    )
    ospf.required_attributes.add(area_attribute)

    return ospf


class TestCreation(object):
    @pytest.fixture
    def device(self, circuit):
        return circuit.endpoint_a.device

    @pytest.fixture
    def interface(self, circuit):
        return circuit.endpoint_a

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


class TestInterfaces(object):
    @pytest.fixture
    def protocol(self, circuit, bgp):
        device = circuit.endpoint_a.device

        return models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type=bgp,
            attributes={
                'asn': '1234',
            }
        )

    @pytest.fixture
    def interface(self, circuit):
        return circuit.endpoint_a

    @pytest.fixture
    def interface_protocol(self, interface, ospf):
        device = interface.device

        return models.Protocol.objects.create(
            device=device,
            interface=interface,
            type=ospf,
            attributes={'area': '1234'},
        )

    def test_local_interface(self, circuit, protocol, interface,
                             interface_protocol):
        assert protocol.local_interface() == circuit.endpoint_a
        assert interface_protocol.local_interface() == interface

    def test_remote_interface(self, circuit, protocol):
        assert protocol.remote_interface() == circuit.endpoint_z

    def test_backwards_circuit(self, circuit, bgp):
        """
        Make sure local/remote_interface returns the correct thing when the
        device is on the Z side of the circuit instead of the A side
        """
        protocol = models.Protocol.objects.create(
            device=circuit.endpoint_z.device,
            circuit=circuit,
            type=bgp,
            attributes={
                'asn': '1234',
            }
        )

        assert protocol.local_interface() == circuit.endpoint_z
        assert protocol.remote_interface() == circuit.endpoint_a
