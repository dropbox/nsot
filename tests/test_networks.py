import pytest

from nsot import models

from .fixtures import session, site


def test_networks_creation_reparenting(session, site):
    net_8  = models.Network.create(session, site.id, u"10.0.0.0/8")
    net_24 = models.Network.create(session, site.id, u"10.0.0.0/24")
    net_16 = models.Network.create(session, site.id, u"10.0.0.0/16")
    net_0  = models.Network.create(session, site.id, u"0.0.0.0/0")

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


def test_network_create_hostbits_set(session, site):
    with pytest.raises(ValueError):
        models.Network.create(session, site.id, u"10.0.0.0/0")


def test_network_attributes(session, site):
    network = models.Network.create(session, site.id, u"10.0.0.0/8", {
        "vlan": "34"
    })

    assert network.attributes == {"vlan": "34"}

    # Verify property successfully zeros out attributes
    network.attributes = {}
    assert network.attributes == {}

    with pytest.raises(TypeError):
        network.attributes = None

    with pytest.raises(ValueError):
        network.attributes = {0: "value"}

    with pytest.raises(ValueError):
        network.attributes = {"key": 0}
