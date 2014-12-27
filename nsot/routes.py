from .handlers import api

HANDLERS = [

    # Sites
    (r"/api/sites", api.SitesHandler),
    (r"/api/sites/(?P<site_id>\d+)", api.SiteHandler),

    # NetworkAttributes
    (r"/api/sites/(?P<site_id>\d+)/network_attributes", api.NetworkAttributesHandler),
    (r"/api/sites/(?P<site_id>\d+)/network_attributes/(?P<attribute_id>\d+)", api.NetworkAttributeHandler),

    # Networks
    (r"/api/sites/(?P<site_id>\d+)/networks", api.NetworksHandler),
    (r"/api/sites/(?P<site_id>\d+)/networks/(?P<network_id>\d+)", api.NetworkHandler),

    # Change Log
    (r"/api/changes", api.ChangesHandler),
    (r"/api/sites/(?P<site_id>\d+)/changes", api.ChangesHandler),

    (r"/.*", api.NotFoundHandler),

]
