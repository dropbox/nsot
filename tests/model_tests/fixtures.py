import pytest

from nsot import models


@pytest.fixture
def session(request, tmpdir):
    db_path = tmpdir.join("nsot.sqlite")
    db_engine = models.get_db_engine("sqlite:///%s" % db_path)

    models.Model.metadata.drop_all(db_engine)
    models.Model.metadata.create_all(db_engine)
    models.Session.configure(bind=db_engine)
    session = models.Session()

    def fin():
        session.close()
    request.addfinalizer(fin)

    return session


@pytest.fixture
def user(session):
    user = models.User(email="gary@localhost").add(session)
    session.commit()
    return user


@pytest.fixture
def admin(session):
    user = models.User(email="admin@localhost").add(session)
    session.commit()
    return user


@pytest.fixture
def site(session, admin):
    site = models.Site.create(
        session, admin.id,
        name="Test Site",
        description="This is a Test Site."
    )
    session.commit()
    return site
