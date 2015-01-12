import ipaddress
import pytest
import time

from nsot import exc
from nsot import models

from model_tests.fixtures import session, admin, site


def test_create_1024(session, admin, site):

    uid = admin.id
    sid = site.id

    address = u"10.0.0.0/22"
    models.Network.create(session, uid, sid, address)
    models.NetworkAttribute.create(session, uid, site_id=sid, name="aaaa")

    start = time.time()
    network = ipaddress.ip_network(address)
    for ip in network.hosts():
        models.Network.create(session, uid, sid, ip.exploded, {
            "aaaa": "value",
        })

    print "Finished in {} seconds.".format(time.time() - start)
