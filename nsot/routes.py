from .handlers import api

HANDLERS = [

    # Sites
    (r"/api/sites", api.SitesHandler),
    (r"/api/sites/(?P<site_id>\d+)", api.SiteHandler),

    # Subnets
    (r"/api/sites/(?P<site_id>\d+)/subnets", api.SubnetsHandler),
    (r"/api/sites/(?P<site_id>\d+)/subnets/(?P<network_id>\d+)", api.SubnetHandler),
    (r"/api/sites/(?P<site_id>\d+)/subnets/(?P<network_id>\d+)/ips", api.SubnetIpsHandler),

    # IP Addresses
    (r"/api/sites/(?P<site_id>\d+)/ips", api.IpsHandler),
    (r"/api/sites/(?P<site_id>\d+)/ips/(?P<network_id>\d+)", api.IpHandler),
    (r"/api/sites/(?P<site_id>\d+)/ips/(?P<network_id>\d+)/subnets", api.IpSubnetsHandler),
    (r"/api/sites/(?P<site_id>\d+)/ips/(?P<network_id>\d+)/hostnames", api.IpHostnamesHandler),

    (r"/.*", api.NotFoundHandler),

]
