from nsot import models

from .fixtures import session, site, user, admin


def test_reparent_bug_issues_27(session, admin, site):
    """
        Test for bug described at https://github.com/dropbox/nsot/issues/27
    """

    net_8  = models.Network.create(session, admin.id, site.id, u"10.0.0.0/8")
    net_31 = models.Network.create(session, admin.id, site.id, u"10.17.244.128/31")
    net_25 = models.Network.create(session, admin.id, site.id, u"10.16.1.0/25")

    assert net_8.parent_id is None
    assert net_31.parent_id == net_8.id
    assert net_25.parent_id == net_8.id
