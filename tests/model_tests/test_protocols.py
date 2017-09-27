# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from nsot import exc, models
from .fixtures import circuit, site


# Allow everything in there to access the DB
pytestmark = pytest.mark.django_db


class TestCreation(object):
    @pytest.fixture
    def device(self, circuit):
        return circuit.endpoint_a.device

    def test_normal_conditions(self, device, circuit):
        """
        Under normal conditions, ensure that a Protocol can be created without
        raising any exceptions
        """
        protocol = models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type='bgp',
            asn=1234,
            description='My fancy peer'
        )

        assert protocol.site_id == device.site_id
        assert protocol in device.protocols.all()
        assert protocol in circuit.protocols.all()

    def test_bad_circuit(self, device, circuit):
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
                type='bgp',
                asn=1234
            )

    def test_bad_type(self, device, circuit):
        with pytest.raises(exc.ValidationError):
            models.Protocol.objects.create(
                device=device,
                circuit=circuit,
                type='oh no',
                asn=1234
            )

    def test_attributes(self, device, circuit):
        """ Ensure that we can set attributes on a Protocol """
        models.Attribute.objects.create(
            site=device.site, resource_name='Protocol', name='import_policies')

        protocol = models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type='bgp',
            asn=1234,
            attributes={
                'import_policies': 'foo'
            }
        )

        assert protocol.get_attributes()['import_policies'] == 'foo'


class TestInterfaces(object):
    @pytest.fixture
    def protocol(self, circuit):
        device = circuit.endpoint_a.device

        return models.Protocol.objects.create(
            device=device,
            circuit=circuit,
            type='bgp',
            asn=1234
        )

    def test_local_interface(self, circuit, protocol):
        assert protocol.local_interface() == circuit.endpoint_a

    def test_remote_interface(self, circuit, protocol):
        assert protocol.remote_interface() == circuit.endpoint_z

    def test_backwards_circuit(self, circuit):
        """
        Make sure local/remote_interface returns the correct thing when the
        device is on the Z side of the circuit instead of the A side
        """
        protocol = models.Protocol.objects.create(
            device=circuit.endpoint_z.device,
            circuit=circuit,
            type='bgp',
            asn=1234
        )

        assert protocol.local_interface() == circuit.endpoint_z
        assert protocol.remote_interface() == circuit.endpoint_a
