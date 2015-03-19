from .handlers import api, fe

HANDLERS = [

    # Sites
    (r"/api/sites", api.SitesHandler),
    (r"/api/sites/(?P<site_id>\d+)", api.SiteHandler),

    # Attributes
    (r"/api/sites/(?P<site_id>\d+)/attributes", api.AttributesHandler),
    (r"/api/sites/(?P<site_id>\d+)/attributes/(?P<attribute_id>\d+)", api.AttributeHandler),

    # Devices
    (r"/api/sites/(?P<site_id>\d+)/devices", api.DevicesHandler),
    (r"/api/sites/(?P<site_id>\d+)/devices/query", api.DevicesQueryHandler),
    (r"/api/sites/(?P<site_id>\d+)/devices/(?P<device_id>\d+)", api.DeviceHandler),

    # Networks
    (r"/api/sites/(?P<site_id>\d+)/networks", api.NetworksHandler),
    (r"/api/sites/(?P<site_id>\d+)/networks/query", api.NetworksQueryHandler),
    (r"/api/sites/(?P<site_id>\d+)/networks/(?P<network_id>\d+)", api.NetworkHandler),
    (   r"/api/sites/(?P<site_id>\d+)/networks/(?P<network_id>\d+)/subnets",
        api.NetworkSubnetsHandler
    ),
    (   r"/api/sites/(?P<site_id>\d+)/networks/(?P<network_id>\d+)/supernets",
        api.NetworkSupernetsHandler
    ),

    # Change Log
    (r"/api/sites/(?P<site_id>\d+)/changes", api.ChangesHandler),
    (r"/api/sites/(?P<site_id>\d+)/changes/(?P<change_id>\d+)", api.ChangeHandler),

    # Users
    (r"/api/users", api.UsersHandler),
    (r"/api/users/(?P<user_id>\d+)", api.UserHandler),
    (r"/api/users/(?P<user_id>\d+)/rotate_secret_key", api.UserRotateSecretKeyHandler),
    (r"/api/users/(?P<user_id>\d+)/permissions", api.UserPermissionsHandler),
    (
        r"/api/users/(?P<user_id>\d+)/permissions/(?P<site_id>\d+)",
        api.UserPermissionHandler
    ),

    # API Auth
    (r"/api/authenticate", api.AuthTokenLoginHandler),
    (r"/api/verify_token", api.AuthTokenVerifyHandler),

    # API fallback
    (r"/api/.*", api.NotFoundHandler),

    # Frontend Handlers
    (r".*", fe.AppHandler),
]
