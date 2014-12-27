import pytest

from nsot import models


@pytest.fixture
def session(request, tmpdir):
    db_path = tmpdir.join("nsot.sqlite")
    db_engine = models.get_db_engine("sqlite:///%s" % db_path)

    models.Model.metadata.create_all(db_engine)
    models.Session.configure(bind=db_engine)
    session = models.Session()

    def fin():
        session.close()
        # Useful if testing against MySQL
        # models.Model.metadata.drop_all(db_engine)
    request.addfinalizer(fin)

    return session


@pytest.fixture
def user(session):
    user = models.User(email="gary@foo").add(session)
    session.commit()
    return user


@pytest.fixture
def site(session, user):
    site = models.Site.create(
        session, user.id,
        name="Test Site",
        description="This is a Test Site."
    )
    session.commit()
    return site
