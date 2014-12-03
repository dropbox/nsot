import json
import os
import pytest

from nsot import models


@pytest.fixture
def session(request, tmpdir):
    db_path = tmpdir.join("nsot.sqlite")
    db_engine = models.get_db_engine("sqlite:///%s" % db_path)

    models.Model.metadata.create_all(db_engine)
    Session.configure(bind=db_engine)
    session = Session()

    def fin():
        session.close()
        # Useful if testing against MySQL
        #models.Model.metadata.drop_all(db_engine)
    request.addfinalizer(fin)

    return session
