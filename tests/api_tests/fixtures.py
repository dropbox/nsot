import logging
import pytest
import socket
import threading
import tornado
import tornado.httpserver
import tornado.ioloop
from tornado import netutil

from nsot import models
from nsot.routes import HANDLERS
from nsot.settings import settings
from nsot.util import Application


sa_log = logging.getLogger("sqlalchemy.engine.base.Engine")

# Uncomment to have all queries printed out
# sa_log.setLevel(logging.INFO)

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
    }

    return Application(HANDLERS, my_settings=my_settings, **tornado_settings)


@pytest.fixture()
def tornado_server(request, tornado_app):

    server = Server(tornado_app)

    def fin():
        tornado.ioloop.IOLoop.instance().stop()
        server.io_thread.join()
    request.addfinalizer(fin)

    return server
