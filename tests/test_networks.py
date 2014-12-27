import pytest

from nsot import exc
from nsot import models

from .fixtures import session, site, user


def test_networks_creation_reparenting(session, user, site):
    net_8  = models.Network.create(session, user.id, site.id, u"10.0.0.0/8")
    net_24 = models.Network.create(session, user.id, site.id, u"10.0.0.0/24")
    net_16 = models.Network.create(session, user.id, site.id, u"10.0.0.0/16")
    net_0  = models.Network.create(session, user.id, site.id, u"0.0.0.0/0")

    assert net_0.parent_id is None
    assert net_8.parent_id == net_0.id
    assert net_16.parent_id == net_8.id
    assert net_24.parent_id == net_16.id

    assert sorted(net_0.supernets(session)) == sorted([])
    assert sorted(net_0.subnets(session)) == sorted([net_8, net_16, net_24])

    assert sorted(net_8.supernets(session)) == sorted([net_0])
    assert sorted(net_8.subnets(session)) == sorted([net_16, net_24])

    assert sorted(net_16.supernets(session)) == sorted([net_0, net_8])
    assert sorted(net_16.subnets(session)) == sorted([net_24])

    assert sorted(net_24.supernets(session)) == sorted([net_0, net_8, net_16])
    assert sorted(net_24.subnets(session)) == sorted([])


def test_network_create_hostbits_set(session, user, site):
    with pytest.raises(ValueError):
        models.Network.create(session, user.id, site.id, u"10.0.0.0/0")


def test_network_attributes(session, user, site):
    models.NetworkAttribute.create(session, user.id, site_id=site.id, name="vlan")

    network = models.Network.create(session, user.id, site.id, u"10.0.0.0/8", {
        "vlan": "34"
    })

    assert network.get_attributes() == {"vlan": "34"}

    # Verify property successfully zeros out attributes
    network.set_attributes({})
    assert network.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        network.set_attributes(None)

    with pytest.raises(exc.ValidationError):
        network.set_attributes({0: "value"})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({"key": 0})

    with pytest.raises(exc.ValidationError):
        network.set_attributes({"made_up": "value"})


def test_ip_address_no_network(session, user, site):
    with pytest.raises(exc.ValidationError):
        models.Network.create(session, user.id, site.id, u"10.0.0.1/32")

    models.Network.create(session, user.id, site.id, u"10.0.0.0/8")
    models.Network.create(session, user.id, site.id, u"10.0.0.1/32")
