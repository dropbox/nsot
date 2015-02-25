import pytest

from nsot import exc
from nsot import models

from .fixtures import session, site, user, admin


def test_device_attributes(session, admin, site):
    models.Attribute.create(
        session, admin.id, site_id=site.id,
        resource_name="Device", name="owner"
    )

    device = models.Device.create(session, admin.id, site.id, "foobarhost", {
        "owner": "gary"
    })

    assert device.get_attributes() == {"owner": "gary"}

    # Verify property successfully zeros out attributes
    device.update(admin.id, attributes={})
    assert device.get_attributes() == {}

    with pytest.raises(exc.ValidationError):
        device.update(admin.id, attributes=None)

    with pytest.raises(exc.ValidationError):
        device.update(admin.id, attributes={0: "value"})

    with pytest.raises(exc.ValidationError):
        device.update(admin.id, attributes={"key": 0})

    with pytest.raises(exc.ValidationError):
        device.update(admin.id, attributes={"made_up": "value"})


def test_retrieve_device(session, admin, site):
    models.Attribute.create(
        session, admin.id, site_id=site.id,
        resource_name="Device", name="test"
    )

    device1 = models.Device.create(
        session, admin.id, site.id, hostname="device1",
        attributes={"test": "foo"}
    )
    device2 = models.Device.create(
        session, admin.id, site.id, hostname="device2",
        attributes={"test": "bar"}
    )
    device3 = models.Device.create(
        session, admin.id, site.id, hostname="device3"
    )

    assert sorted(site.devices()) == sorted([device1, device2, device3])

    with pytest.raises(ValueError):
        assert site.devices(attribute_value="foo")

    assert sorted(site.devices(
        attribute_name="test"
    )) == sorted([device1, device2])

    assert sorted(site.devices(
        attribute_name="test", attribute_value="foo"
    )) == sorted([device1])
