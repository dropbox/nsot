import pytest
from sqlalchemy.exc import IntegrityError

from nsot import exc
from nsot import models

from .fixtures import session, site, user, admin


def test_creation(session, site, admin):
    models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="test_attribute"
    )
    session.commit()

    attributes = session.query(models.Attribute).all()
    assert len(attributes) == 1
    assert attributes[0].id == 1
    assert attributes[0].site_id == site.id
    assert attributes[0].name == "test_attribute"
    assert attributes[0].required == False


def test_conflict(session, site, admin):
    models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="test_attribute"
    )

    with pytest.raises(IntegrityError):
        models.Attribute.create(
            session, admin.id,
            resource_name="Network",
            site_id=site.id, name="test_attribute"
        )

    models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="test_attribute_2"
    )


def test_validation(session, site, admin):
    with pytest.raises(exc.ValidationError):
        models.Attribute.create(
            session, admin.id,
            resource_name="Network",
            site_id=site.id, name=None,
        )

    with pytest.raises(exc.ValidationError):
        models.Attribute.create(
            session, admin.id,
            resource_name="Network",
            site_id=site.id, name="",
        )

    attribute = models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="test_attribute"
    )

    with pytest.raises(exc.ValidationError):
        attribute.update(admin.id, name="")

    with pytest.raises(exc.ValidationError):
        attribute.update(admin.id, name=None)

    attribute.update(admin.id, name="test_attribute_new")
    session.commit()


def test_deletion(session, site, admin):
    attribute = models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="test_attribute"
    )

    network = models.Network.create(
        session, admin.id, site.id,
        cidr=u"10.0.0.0/8", attributes={"test_attribute": "foo"}
    )

    with pytest.raises(IntegrityError):
        attribute.delete(admin.id)

    network.delete(admin.id)
    attribute.delete(admin.id)


def test_required(session, site, admin):
    attribute_1 = models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="required_1", required=True
    )

    attribute_2 = models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="required_2", required=True
    )

    with pytest.raises(exc.ValidationError):
        network = models.Network.create(
            session, admin.id, site.id,
            cidr=u"10.0.0.0/8"
        )

    with pytest.raises(exc.ValidationError):
        network = models.Network.create(
            session, admin.id, site.id,
            cidr=u"10.0.0.0/8", attributes={
                "required_1": "foo",
            }
        )

    network = models.Network.create(
        session, admin.id, site.id,
        cidr=u"10.0.0.0/8", attributes={
            "required_1": "foo",
            "required_2": "bar",
        }
    )


def test_multi(session, site, admin):
    multi = models.Attribute.create(
        session, admin.id,
        resource_name="Network", display=True,
        site_id=site.id, name="multi", multi=True
    )

    not_multi = models.Attribute.create(
        session, admin.id,
        resource_name="Network",
        site_id=site.id, name="not_multi", multi=False
    )

    models.Network.create(session, admin.id, site.id, cidr=u"10.0.0.0/8")

    models.Network.create(
        session, admin.id, site.id, cidr=u"10.0.0.1",
        attributes={
            "multi": ["test", "testing", "testtttt"]
        }
    )

    with pytest.raises(exc.ValidationError):
        models.Network.create(
            session, admin.id, site.id, cidr=u"10.0.0.2",
            attributes={
                "not_multi": ["test", "testing", "testtttt"]
            }
        )


def test_constraints(session, site, admin):
    default = models.Attribute.create(
        session, admin.id,
        resource_name="Network", site_id=site.id, name="default"
    )

    allow_empty = models.Attribute.create(
        session, admin.id,
        resource_name="Network", site_id=site.id, name="allow_empty",
        constraints={"allow_empty": True}
    )

    pattern = models.Attribute.create(
        session, admin.id,
        resource_name="Network", site_id=site.id, name="pattern",
        constraints={"pattern": "\d\d\d+"}
    )

    valid = models.Attribute.create(
        session, admin.id,
        resource_name="Network", site_id=site.id, name="valid",
        constraints={"valid_values": ["foo", "bar", "baz"]}
    )

    # Test that ValidationError is raised when constraints are not a dict
    with pytest.raises(exc.ValidationError):
        models.Attribute.create(
            session, admin.id, resource_name='Network', site_id='site.id',
            name='invalid', constraints=['foo', 'bar', 'baz']
        )

    network = models.Network.create(session, admin.id, site.id, cidr=u"10.0.0.0/8")

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"default": ""})

    # Test allow_empty
    network.update(admin.id, attributes={"allow_empty": ""})

    # Test pattern
    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"pattern": ""})

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"pattern": "foo"})

    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"pattern": "10"})

    network.update(admin.id, attributes={"pattern": "100"})
    network.update(admin.id, attributes={"pattern": "1000000"})

    # Test valid_values
    with pytest.raises(exc.ValidationError):
        network.update(admin.id, attributes={"valid": "hello"})

    network.update(admin.id, attributes={"valid": "foo"})
