import pytest

from nsot import exc
from nsot import models

from .fixtures import session, site, user, admin


def test_networks_creation_reparenting(session, admin, site):
    net_8  = models.Network.create(session, admin.id, site.id, u"10.0.0.0/8")
    net_24 = models.Network.create(session, admin.id, site.id, u"10.0.0.0/24")
    net_16 = models.Network.create(session, admin.id, site.id, u"10.0.0.0/16")
    net_0  = models.Network.create(session, admin.id, site.id, u"0.0.0.0/0")

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


def test_seqential_creation(session, admin, site):
    net_8 = models.Network.create(session, admin.id, site.id, u"10.0.0.0/8")
    net_22_1 = models.Network.create(session, admin.id, site.id, u"10.0.0.0/22")
    net_22_2 = models.Network.create(session, admin.id, site.id, u"10.0.4.0/22")
    net_22_3 = models.Network.create(session, admin.id, site.id, u"10.0.8.0/22")

    assert net_8.id == net_22_1.parent_id
    assert net_8.id == net_22_2.parent_id
    assert net_8.id == net_22_3.parent_id


def test_network_create_hostbits_set(session, admin, site):
    with pytest.raises(ValueError):
        models.Network.create(session, admin.id, site.id, u"10.0.0.0/0")


def test_network_attributes(session, admin, site):
    models.Attribute.create(
        session, admin.id, site_id=site.id,
        resource_name="Network", name="vlan"
    )

    network = models.Network.create(session, admin.id, site.id, u"10.0.0.0/8", {
        "vlan": "34"
    })

    assert network.get_attributes() == {"vlan": "34"}

    # Verify property successfully zeros out attributes
    network.update(admin.id, attributes={})
    assert network.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes=None)

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={0: "value"})

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"key": 0})

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"made_up": "value"})


def test_ip_address_no_network(session, admin, site):
    with pytest.raises(exc.ValidationError):
        models.Network.create(session, admin.id, site.id, u"10.0.0.1/32")

    models.Network.create(session, admin.id, site.id, u"10.0.0.0/8")
    models.Network.create(session, admin.id, site.id, u"10.0.0.1/32")

def test_retrieve_networks(session, admin, site):
    models.Attribute.create(
        session, admin.id, site_id=site.id,
        resource_name="Network", name="test"
    )

    net_8 = models.Network.create(
        session, admin.id, site.id, cidr=u"10.0.0.0/8",
        attributes={"test": "foo"}
    )
    net_24 = models.Network.create(
        session, admin.id, site.id, cidr=u"10.0.0.0/24",
        attributes={"test": "bar"}
    )
    ip = models.Network.create(
        session, admin.id, site.id, cidr=u"10.0.0.1/32"
    )

    assert sorted(site.networks(
        root=True
    )) == sorted([net_8])

    assert sorted(site.networks(
        include_networks=True, include_ips=False
    )) == sorted([net_8, net_24])

    assert sorted(site.networks(
        include_networks=False, include_ips=False
    )) == sorted([])

    assert sorted(site.networks(
        include_networks=True, include_ips=True
    )) == sorted([net_8, net_24, ip])

    assert sorted(site.networks(
        include_networks=False, include_ips=True
    )) == sorted([ip])

    assert sorted(site.networks(
        subnets_of="10.0.0.0/10"
    )) == sorted([net_24])

    assert sorted(site.networks(
        subnets_of="10.0.0.0/10", include_ips=True
    )) == sorted([net_24, ip])

    assert sorted(site.networks(
        supernets_of="10.0.0.0/10"
    )) == sorted([net_8])

    with pytest.raises(ValueError):
        site.networks(subnets_of="10.0.0.0/10", supernets_of="10.0.0.0/10")

    with pytest.raises(ValueError):
        assert site.networks(attribute_value="foo")

    assert sorted(site.networks(
        include_ips=True, attribute_name="test"
    )) == sorted([net_8, net_24])

    assert sorted(site.networks(
        include_ips=True, attribute_name="test", attribute_value="foo"
    )) == sorted([net_8])
