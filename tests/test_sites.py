import pytest
from sqlalchemy.exc import IntegrityError

from nsot import exc
from nsot import models

from .fixtures import session, user


def test_site_creation(session, user):
    models.Site.create(
        session, user.id,
        name="Test Site",
        description="This is a Test Site."
    )
    session.commit()

    sites = session.query(models.Site).all()
    assert len(sites) == 1
    assert sites[0].id == 1
    assert sites[0].name == "Test Site"
    assert sites[0].description == "This is a Test Site."


def test_site_conflict(session, user):
    models.Site.create(
        session, user.id,
        name="Test Site",
        description="This is a Test Site."
    )

    with pytest.raises(IntegrityError):
        models.Site.create(
            session, user.id,
            name="Test Site",
            description="This is a Test Site."
        )

    models.Site.create(
        session, user.id,
        name="Test Site 2",
        description="This is a Test Site."
    )


def test_site_validation(session, user):
    with pytest.raises(exc.ValidationError):
        models.Site.create(
            session, user.id,
            name=None,
            description="This is a Test Site."
        )

    with pytest.raises(exc.ValidationError):
        models.Site.create(
            session, user.id,
            name="",
            description="This is a Test Site."
        )

    site = models.Site.create(
        session, user.id,
        name="Test Site",
        description="This is a Test Site."
    )

    with pytest.raises(exc.ValidationError):
        site.update(user.id, name="")

    with pytest.raises(exc.ValidationError):
        site.update(user.id, name=None)

    site.update(user.id, name="Test Site New")
    session.commit()
