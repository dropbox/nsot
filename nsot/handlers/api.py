from sqlalchemy.exc import IntegrityError


from .util import ApiHandler
from .. import exc
from ..decorators import any_perm
from .. import models
from ..util import qp_to_bool as qpbool


class SitesHandler(ApiHandler):

    def post(self):
        """ **Create a Site**

        **Example Request**:

        .. sourcecode:: http

            POST /api/sites HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "name": "New Site",
                "description": "This is our new Site."
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 OK
            Location: /api/sites/1

        :reqjson string name: The name of the Site
        :reqjson string description: (*optional*) A helpful description for the Site

        :reqheader Content-Type: The server expects a json body specified with
                                 this header.
        :reqheader X-NSoT-Email: required for all api requests.

        :resheader Location: URL to the created resource.

        :statuscode 201: The site was successfully created.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 409: There was a conflict with another resource.
        """

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description", "")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))
        except ValueError as err:
            return self.badrequest(err.message)

        try:
            site = models.Site.create(
                self.session, self.current_user.id, name=name, description=description
            )
        except IntegrityError as err:
            return self.conflict(err.orig.message)
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.created("/api/sites/{}".format(site.id))

    def get(self):
        """ **Get all Sites**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "sites": [
                        {
                            "id": 1
                            "name": "Site 1",
                            "description": ""
                        }
                    ]
                }
            }

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        """
        sites = self.session.query(models.Site).all()
        self.success({
            "sites": [site.to_dict() for site in sites],
        })


class SiteHandler(ApiHandler):
    def get(self, site_id):
        """ **Get a specific Site**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "site": {
                        "id": 1,
                        "name": "Site 1",
                        "description": ""
                    }
                }
            }

        :param site_id: ID of the Site to retrieve
        :type site_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))
        self.success({
            "site": site.to_dict(),
        })

    @any_perm("admin")
    def put(self, site_id):
        """ **Update a Site**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/sites/1 HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "name": "Old Site",
                "description": "A better description."
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "site": {
                        "id": 1,
                        "name": "Old Site",
                        "description": "A better description."
                    }
                }
            }


        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :reqheader Content-Type: The server expects a json body specified with
                                 this header.
        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site at site_id was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description", "")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            site.update(
                self.current_user.id,
                name=name, description=description
            )
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.success({
            "site": site.to_dict(),
        })

    @any_perm("admin")
    def delete(self, site_id):
        """ **Delete a Site**

        **Example Request**:

        .. sourcecode:: http

            DELETE /api/sites/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "message": Site 1 deleted."
                }
            }


        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site at site_id was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        try:
            site.delete(self.current_user.id)
        except IntegrityError as err:
            return self.conflict(err.orig.message)

        self.success({
            "message": "Site {} deleted.".format(site_id),
        })


class NetworkAttributesHandler(ApiHandler):

    @any_perm("admin", "network_attrs")
    def post(self, site_id):
        """ **Create a Network Attribute**

        **Example Request**:

        .. sourcecode:: http

            POST /api/sites/1/network_attributes HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "name": "owner",
                "description": "This is our new Site.",
                "required": false
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 OK
            Location: /api/sites/1/network_attributes/1

        :param site_id: ID of the Site where this should be created.
        :type site_id: int

        :reqjson string name: The name of the Attribute
        :reqjson string description: (*optional*) A helpful description of
                                     the Attribute
        :reqjson bool required: (*optional*) Whether this attribute should be required.

        :reqheader Content-Type: The server expects a json body specified with
                                 this header.
        :reqheader X-NSoT-Email: required for all api requests.

        :resheader Location: URL to the created resource.

        :statuscode 201: The site was successfully created.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site at site_id was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description")
            required = qpbool(self.jbody.get("required"))
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute = models.NetworkAttribute.create(
                self.session, self.current_user.id,
                site_id=site_id, name=name, description=description,
                required=required
            )
        except IntegrityError as err:
            return self.conflict(str(err.orig))
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.created("/api/sites/{}/network_attributes/{}".format(
            site_id, attribute.id
        ))

    def get(self, site_id):
        """ **Get all Network Attributes**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/network_attributes HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "network_attributes": [
                        {
                            "id": 1,
                            "site_id": 1,
                            "name": "vlan",
                            "description": "",
                            "required": false
                        }
                    ]
                }
            }

        :param site_id: ID of the Site to retrieve Network Attributes from.
        :type site_id: int

        :query string name: (*optional*) Filter to attribute with name
        :query bool required: (*optional*) Filter to attributes that are required

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        name = self.get_argument("name", None)
        required = qpbool(self.get_argument("required", None))

        attributes = self.session.query(models.NetworkAttribute).filter_by(
            site_id=site_id
        )

        if name is not None:
            attributes = attributes.filter_by(name=name)

        if required:
            attributes = attributes.filter_by(required=True)

        self.success({
            "network_attributes": [attribute.to_dict() for attribute in attributes],
        })


class NetworkAttributeHandler(ApiHandler):
    def get(self, site_id, attribute_id):
        """ **Get a specific Network Attribute**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/network_attributes/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "network_attribute": {
                        "id": 1,
                        "site_id": 1,
                        "name": "vlan",
                        "description": "",
                        "required": false
                    }
                }
            }

        :param site_id: ID of the Site this Attribute is under.
        :type site_id: int

        :param attribute_id: ID of the NetworkAttribute being retrieved.
        :type attribute_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Attribute was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.NetworkAttribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            return self.notfound(
                "No such NetworkAttribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        self.success({
            "network_attribute": attribute.to_dict(),
        })

    @any_perm("admin", "network_attrs")
    def put(self, site_id, attribute_id):
        """ **Update a Network Attribute**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/sites/1/network_attributes/1 HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "description": "Attribute Description",
                "required": true
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "network_attribute": {
                        "id": 1,
                        "name": "vlan",
                        "description": "Attribute Description",
                        "required": true
                    }
                }
            }


        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param attribute_id: ID of the NetworkAttribute being updated.
        :type attribute_id: int

        :reqjson string description: (*optional*) A helpful description of
                                     the Attribute
        :reqjson bool required: (*optional*) Whether this attribute should be required.

        :reqheader Content-Type: The server expects application/json.
        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or Attribute was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.NetworkAttribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            return self.notfound(
                "No such NetworkAttribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        try:
            description = self.jbody.get("description", "")
            required = qpbool(self.jbody.get("required"))
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute.update(
                self.current_user.id,
                description=description, required=required,
            )
        except IntegrityError as err:
            return self.conflict(str(err.orig))
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.success({
            "network_attribute": attribute.to_dict(),
        })

    @any_perm("admin", "network_attrs")
    def delete(self, site_id, attribute_id):
        """ **Delete a Network Attribute**

        **Example Request**:

        .. sourcecode:: http

            DELETE /api/sites/1/network_attribute/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "message": NetworkDeleted 1 deleted."
                }
            }


        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param attribute_id: ID of the NetworkAttribute being deleted.
        :type attribute_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or Attribute was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.NetworkAttribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            return self.notfound(
                "No such NetworkAttribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        try:
            attribute.delete(self.current_user.id)
        except IntegrityError as err:
            return self.conflict(err.orig.message)

        self.success({
            "message": "NetworkAttribute {} deleted from Site {}.".format(
                attribute_id, site_id
            ),
        })


class NetworksHandler(ApiHandler):

    @any_perm("admin", "networks")
    def post(self, site_id):
        """ **Create a Network**

        **Example Request**:

        .. sourcecode:: http

            POST /api/sites/1/networks HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "cidr": "10.0.0.0/8",
                "attributes": {
                    "vlan": "23"
                }
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 OK
            Location: /api/sites/1/networks/1

        :param site_id: ID of the Site where this should be created.
        :type site_id: int

        :reqjson string cidr: A network or ip address in CIDR notation.
        :reqjson object attributes: (*optional*) An object of key/value pairs
                                    attached to this network.

        :reqheader Content-Type: The server expects a json body specified with
                                 this header.
        :reqheader X-NSoT-Email: required for all api requests.

        :resheader Location: URL to the created resource.

        :statuscode 201: The site was successfully created.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site at site_id was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        try:
            cidr = self.jbody["cidr"]
            attributes = self.jbody.get("attributes", {})
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            network = models.Network.create(
                self.session, self.current_user.id, site_id,
                cidr=cidr, attributes=attributes,
            )
        except IntegrityError as err:
            return self.conflict(err.orig.message)
        except (ValueError, exc.ValidationError) as err:
            return self.badrequest(err.message)

        self.created("/api/sites/{}/networks/{}".format(site_id, network.id))

    def get(self, site_id):
        """ Return all Networks. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        root_only = qpbool(self.get_argument("root_only", False))
        include_networks = qpbool(self.get_argument("include_networks", True))
        include_ips = qpbool(self.get_argument("include_ips", False))

        networks = site.networks(
            root=root_only, include_ips=include_ips,
            include_networks=include_networks
        )

        self.success({
            "networks": [network.to_dict() for network in networks],
        })


class NetworkHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return a specific Network. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            return self.notfound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        self.success({
            "network": network.to_dict(),
        })

    @any_perm("admin", "networks")
    def put(self, site_id, network_id):
        """ Update a Network. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            return self.notfound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        try:
            attributes = self.jbody.get("attributes", {})
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            network.update(self.current_user.id, attributes=attributes)
        except IntegrityError as err:
            return self.conflict(err.orig.message)
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.success({
            "network": network.to_dict(),
        })

    @any_perm("admin", "networks")
    def delete(self, site_id, network_id):
        """ Delete a Network. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            return self.notfound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        try:
            network.delete(self.current_user.id)
        except IntegrityError as err:
            return self.conflict(err.orig.message)

        self.success({
            "message": "Network {} deleted from Site {}.".format(
                network_id, site_id
            ),
        })

class NetworkSubnetsHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return subnets of a specific Network. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            return self.notfound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        direct = qpbool(self.get_argument("direct", False))
        include_networks = qpbool(self.get_argument("include_networks", True))
        include_ips = qpbool(self.get_argument("include_ips", False))

        networks = network.subnets(
            self.session, direct=direct,
            include_ips=include_ips, include_networks=include_networks
        )

        self.success({
            "networks": [network.to_dict() for network in networks],
        })


class NetworkSupernetsHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return supernets of a specific Network. """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            return self.notfound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        direct = qpbool(self.get_argument("direct", False))

        networks = network.supernets(self.session, direct=direct)

        self.success({
            "networks": [network.to_dict() for network in networks],
        })


class ChangesHandler(ApiHandler):
    def get(self, site_id=None):
        """ Return Change events."""

        event = self.get_argument("event", None)
        if event is not None and event not in models.CHANGE_EVENTS:
            return self.badrequest("Invalid event.")

        resource_type = self.get_argument("resource_type", None)
        if resource_type is not None and resource_type not in models.RESOURCE_BY_NAME:
            return self.badrequest("Invalid resource type.")

        resource_id = self.get_argument("resource_id", None)
        if resource_id is not None and resource_type is None:
            return self.badrequest("resource_id requires resource_type to be set.")

        changes = self.session.query(models.Change)

        if site_id is not None:
            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                return self.notfound("No such Site found at id {}".format(site_id))
            changes = changes.filter_by(site_id=site_id)

        if event is not None:
            changes = changes.filter_by(event=event)

        if resource_type is not None:
            changes = changes.filter_by(resource_type=resource_type)

        if resource_id is not None:
            changes = changes.filter_by(resource_id=resource_id)


        self.success({
            "changes": [change.to_dict() for change in changes],
        })


class UsersHandler(ApiHandler):
    def get(self):
        """ Return Users."""

        users = self.session.query(models.User)

        self.success({
            "users": [user.to_dict() for user in users],
        })

class UserHandler(ApiHandler):
    def get(self, user_id):
        """ Return a User."""

        user = self.session.query(models.User).filter_by(
            id=user_id,
        ).scalar()

        if not user:
            return self.notfound(
                "No such User found at (id) = ({})".format(user_id)
            )

        self.success({
            "user": user.to_dict(),
        })

class UserPermissionsHandler(ApiHandler):
    def get(self, user_id):
        """ Return available Permissions for a User."""

        permissions = self.session.query(models.Permission).filter_by(
            user_id=user_id
        )

        self.success({
            "permissions": [permission.to_dict() for permission in permissions],
        })

class UserPermissionHandler(ApiHandler):
    def get(self, user_id, site_id):
        """ Return Site permissions for a User."""

        permission = self.session.query(models.Permission).filter_by(
            user_id=user_id, site_id=site_id
        ).scalar()

        if not permission:
            return self.notfound(
                "No such Permission found at (user_id, site_id) = ({})".format(
                    user_id, site_id
                )
            )

        self.success({
            "permission": permission.to_dict(),
        })

    @any_perm("admin")
    def put(self, user_id, site_id):
        permission = self.session.query(models.Permission).filter_by(
                user_id=user_id, site_id=site_id
        ).scalar()

        # If the permission exists it's safe to assume the user/site exists. If not
        # we're adding a new permission so verify that the user/site are valid.
        if not permission:
            user = self.session.query(models.User).filter_by(id=user_id).scalar()
            if not user:
                return self.notfound("No such User found at (id) = ({})".format(user_id))

            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                return self.notfound("No such Site found at id {}".format(site_id))

        try:
            permissions = self.jbody["permissions"]
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            if not permission:
                permission = models.Permission.create(
                    self.session, self.current_user.id,
                    user_id=user.id, site_id=site_id,
                    permissions=permissions
                )
            else:
                permission.update(
                    self.current_user.id,
                    permissions=permissions
                )
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.success({
            "permission": permission.to_dict(),
        })


class NotFoundHandler(ApiHandler):
    def get(self):
        return self.notfound("Endpoint not found")
