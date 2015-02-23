import base64
import json
import logging
import os
import pytest
import requests
import socket
import threading
import tornado
import tornado.httpserver
import tornado.ioloop
from tornado import netutil

from nsot import models
from nsot.settings import settings
from nsot.app import Application


sa_log = logging.getLogger("sqlalchemy.engine.base.Engine")

# Uncomment to have all queries printed out
# sa_log.setLevel(logging.INFO)

# Overload the server's secret_key with a randomly-generated one.
SECRET_KEY = base64.urlsafe_b64encode(os.urandom(32))
settings.settings['secret_key'] = SECRET_KEY


class Server(object):
    """ Wrapper around Tornado server with test helpers. """

    def __init__(self, tornado_app):
        self.server = tornado.httpserver.HTTPServer(
            tornado_app
        )
        self.server.add_sockets(netutil.bind_sockets(
            None, "localhost", family=socket.AF_INET
        ))
        self.server.start()
        self.io_thread = threading.Thread(
            target=tornado.ioloop.IOLoop.instance().start
        )
        self.io_thread.start()

    @property
    def port(self):
        return self.server._sockets.values()[0].getsockname()[1]


@pytest.fixture()
def tornado_app(request, tmpdir):
    db_path = tmpdir.join("nsot.sqlite")
    db_engine = models.get_db_engine("sqlite:///%s" % db_path)

    models.Model.metadata.drop_all(db_engine)
    models.Model.metadata.create_all(db_engine)
    models.Session.configure(bind=db_engine)

    my_settings = {
        "db_engine": db_engine,
        "db_session": models.Session,
    }

    tornado_settings = {
        "debug": False,
        "cookie_secret": "dropbox",
        "secret_key": SECRET_KEY,  # Setting secret_key here does nothing?!
    }

    return Application(my_settings=my_settings, **tornado_settings)


@pytest.fixture()
def tornado_server(request, tornado_app):

    server = Server(tornado_app)

    def fin():
        tornado.ioloop.IOLoop.instance().stop()
        server.io_thread.join()
    request.addfinalizer(fin)

    return server


## Forklifted from tests/model_tests/fixtures.py.
##
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
    """Create a user that we can work with."""
    user = models.User(email="gary@localhost").add(session)
    session.commit()
    return user
##
## END Forklifting


@pytest.fixture
def auth_token(tornado_server, user):
    """Token used to test resources requiring auth_token authentication."""
    payload = {"email": user.email, "secret_key": user.secret_key}
    data = json.dumps(payload)
    r = requests.post(
        "http://localhost:{}/api/authenticate".format(tornado_server.port),
        headers={"Content-Type": "application/json"},
        data=data,
    )
    return r.json()['data']['auth_token']
