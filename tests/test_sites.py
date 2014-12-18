import pytest

from nsot import models

from .fixtures import session


def test_site_creation(session):
    models.Site(
        name="Test Site",
        description="This is a Test Site."
    ).add(session)
    session.commit()

    sites = session.query(models.Site).all()
    assert len(sites) == 1
    assert sites[0].id == 1
    assert sites[0].name == "Test Site"
    assert sites[0].description == "This is a Test Site."
