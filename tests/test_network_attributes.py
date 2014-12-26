import pytest
from sqlalchemy.exc import IntegrityError

from nsot import exc
from nsot import models

from .fixtures import session, site, user


def test_creation(session, site, user):
    models.NetworkAttribute.create(
        session, user.id,
        site_id=site.id, name="Test NetworkAttribute"
    )
    session.commit()

    attributes = session.query(models.NetworkAttribute).all()
    assert len(attributes) == 1
    assert attributes[0].id == 1
    assert attributes[0].site_id == site.id
    assert attributes[0].name == "Test NetworkAttribute"
    assert attributes[0].required == False


def test_conflict(session, site, user):
    models.NetworkAttribute.create(
        session, user.id,
        site_id=site.id, name="Test NetworkAttribute"
    )

    with pytest.raises(IntegrityError):
        models.NetworkAttribute.create(
            session, user.id,
            site_id=site.id, name="Test NetworkAttribute"
        )

    models.NetworkAttribute.create(
        session, user.id,
        site_id=site.id, name="Test NetworkAttribute 2"
    )


def test_site_validation(session, site, user):
    with pytest.raises(exc.ValidationError):
        models.NetworkAttribute.create(
            session, user.id,
            site_id=site.id, name=None,
        )

    with pytest.raises(exc.ValidationError):
        models.NetworkAttribute.create(
            session, user.id,
            site_id=site.id, name="",
        )

    attribute = models.NetworkAttribute.create(
        session, user.id,
        site_id=site.id, name="Test NetworkAttribute"
    )

    with pytest.raises(exc.ValidationError):
        attribute.name = ""

    with pytest.raises(exc.ValidationError):
        attribute.name = None

    attribute.name = "Test NetworkAttribute New"
    session.commit()
