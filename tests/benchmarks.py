import ipaddress
import pytest
import time

from nsot import exc
from nsot import models

from model_tests.fixtures import session, admin, site


def test_create_1024(session, admin, site):

    uid = admin.id
    sid = site.id

    address = u"10.0.0.0/20"
    models.Network.create(session, uid, sid, address)
    models.Attribute.create(session, uid, resource_name="Network", site_id=sid, name="aaaa")

    start = time.time()
    network = ipaddress.ip_network(address)
    for ip in network.subnets(new_prefix=30):
        models.Network.create(session, uid, sid, ip.exploded, {
            "aaaa": "value",
        }, commit=False)
    session.commit()

    print "Finished in {} seconds.".format(time.time() - start)
