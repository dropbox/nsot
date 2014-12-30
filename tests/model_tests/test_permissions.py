import pytest
from sqlalchemy.exc import IntegrityError

from nsot import exc
from nsot import models

from .fixtures import session, user, admin, site


def test_permission_creation(session, user, site):
    models.Permission.create(
        session, user.id,
        user_id=user.id, site_id=site.id,
        permissions=0
    )

    permission = session.query(models.Permission).filter_by(
        site_id=site.id, user_id=user.id
    ).scalar()

    assert permission.user_id == user.id
    assert permission.site_id == site.id
    assert permission.permissions == 0


def test_permission_conflict(session, user, site):
    models.Permission.create(
        session, user.id,
        user_id=user.id, site_id=site.id,
        permissions=0
    )

    with pytest.raises(IntegrityError):
        models.Permission.create(
            session, user.id,
            user_id=user.id, site_id=site.id,
            permissions=1
        )

def test_permission_update(session, user, site):
    perm = models.Permission.create(
        session, user.id,
        user_id=user.id, site_id=site.id,
        permissions=0
    )

    perm.update(user.id, permissions=1)

    assert perm.permissions == 1
