from sqlalchemy import desc
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

            {
                "status": "ok",
                "data": {
                    "site": {
                        "id": 1,
                        "name": "New Site",
                        "description": "This is our new Site."
                    }
                }
            }

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
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))
        except ValueError as err:
            raise exc.BadRequest(err.message)

        try:
            site = models.Site.create(
                self.session, self.current_user.id, name=name, description=description
            )
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)

        self.created("/api/sites/{}".format(site.id), {
            "site": site.to_dict(),
        })

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
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :reqheader X-NSoT-Email: required for all api requests.

        :query string name: (*optional*) Filter to site with name.
        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        """
        name = self.get_argument("name", None)

        sites = self.session.query(models.Site)
        if name is not None:
            sites = sites.filter_by(name=name)

        offset, limit = self.get_pagination_values()
        sites, total = self.paginate_query(sites, offset, limit)

        self.success({
            "sites": [site.to_dict() for site in sites.all()],
            "limit": limit,
            "offset": offset,
            "total": total,
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
            raise exc.NotFound("No such Site found at id {}".format(site_id))
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


        :permissions: * **admin**

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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description", "")
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            site.update(
                self.current_user.id,
                name=name, description=description
            )
        except IntegrityError as err:
            raise exc.Conflict(str(err.orig))

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

        :permissions: * **admin**

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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        try:
            site.delete(self.current_user.id)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)

        self.success({
            "message": "Site {} deleted.".format(site_id),
        })


class AttributesHandler(ApiHandler):

    @any_perm("admin")
    def post(self, site_id):
        """ **Create an Attribute**

        **Example Request**:

        .. sourcecode:: http

            POST /api/sites/1/attributes HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "name": "owner",
                "description": "Owner Attribute.",
                "resource_name": "Network",
                "required": false
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 OK
            Location: /api/sites/1/attributes/1

            {
                "status": "ok",
                "data": {
                    "attribute": {
                        "id": 1,
                        "name": "owner",
                        "description": "Owner Attribute.",
                        "resource_name": "Network",
                        "required": false,
                        "display": false,
                        "multi": false,
                        "constraints": {
                            "allow_empty": false,
                            "pattern": "",
                            "valid_values": []
                        }
                    }
                }
            }

        :permissions: * **admin**

        :param site_id: ID of the Site where this should be created.
        :type site_id: int

        :reqjson string name: The name of the Attribute
        :reqjson string resource_name: The type of resource this attribute is for (e.g. Network)
        :reqjson string description: (*optional*) A helpful description of
                                     the Attribute
        :reqjson bool required: (*optional*) Whether this attribute should be required.
        :reqjson bool display: (*optional*) Whether this attribute should be be displayed
                               by default in UIs.
        :reqjson bool multi: (*optional*) Whether the attribute should be treated as a
                             list type.

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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        try:
            name = self.jbody["name"]
            resource_name = self.jbody["resource_name"]
            description = self.jbody.get("description")
            required = self.jbody.get("required", False)
            display = self.jbody.get("display", False)
            multi = self.jbody.get("multi", False)
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute = models.Attribute.create(
                self.session, self.current_user.id,
                site_id=site_id, name=name, description=description,
                resource_name=resource_name, required=required, display=display,
                multi=multi
            )
        except IntegrityError as err:
            raise exc.Conflict(str(err.orig))
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)

        self.created("/api/sites/{}/attributes/{}".format(
            site_id, attribute.id
        ), {
            "attribute": attribute.to_dict(),
        })

    def get(self, site_id):
        """ **Get all Attributes**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/attributes HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "attributes": [
                        {
                            "id": 1,
                            "site_id": 1,
                            "name": "vlan",
                            "description": "",
                            "resource_name": "Network",
                            "required": false,
                            "display": false,
                            "multi": false,
                            "constraints": {
                                "allow_empty": false,
                                "pattern": "",
                                "valid_values": []
                            }
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Attributes from.
        :type site_id: int

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.
        :query string name: (*optional*) Filter to attribute with name
        :query bool required: (*optional*) Filter to attributes that are required
        :query bool display: (*optional*) Filter to attributes meant to be displayed.
        :query bool multi: (*optional*) Filter on whether list type or not

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        name = self.get_argument("name", None)
        resource_name = self.get_argument("resource_name", None)
        required = self.get_argument("required", None)
        display = self.get_argument("display", None)
        multi = self.get_argument("multi", None)

        attributes = self.session.query(models.Attribute).filter_by(
            site_id=site_id
        )

        if name is not None:
            attributes = attributes.filter_by(name=name)
        if resource_name is not None:
            attributes = attributes.filter_by(resource_name=resource_name)
        if required is not None:
            attributes = attributes.filter_by(required=qpbool(required))
        if display is not None:
            attributes = attributes.filter_by(display=qpbool(display))
        if multi is not None:
            attributes = attributes.filter_by(multi=qpbool(multi))

        offset, limit = self.get_pagination_values()
        attributes, total = self.paginate_query(attributes, offset, limit)

        self.success({
            "attributes": [attribute.to_dict() for attribute in attributes],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class AttributeHandler(ApiHandler):
    def get(self, site_id, attribute_id):
        """ **Get a specific Attribute**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/attributes/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "attribute": {
                        "id": 1,
                        "site_id": 1,
                        "name": "vlan",
                        "description": "",
                        "resource_name": "Network",
                        "required": false,
                        "display": false,
                        "multi": false,
                        "constraints": {
                            "allow_empty": false,
                            "pattern": "",
                            "valid_values": []
                        }
                    }
                }
            }

        :param site_id: ID of the Site this Attribute is under.
        :type site_id: int

        :param attribute_id: ID of the Attribute being retrieved.
        :type attribute_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Attribute was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            raise exc.NotFound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        self.success({
            "attribute": attribute.to_dict(),
        })

    @any_perm("admin")
    def put(self, site_id, attribute_id):
        """ **Update an Attribute**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/sites/1/attributes/1 HTTP/1.1
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
                    "attribute": {
                        "id": 1,
                        "name": "vlan",
                        "description": "Attribute Description",
                        "resource_name": "Network",
                        "required": true,
                        "display": false,
                        "multi": false,
                        "constraints": {
                            "allow_empty": false,
                            "pattern": "",
                            "valid_values": []
                        }
                    }
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param attribute_id: ID of the Attribute being updated.
        :type attribute_id: int

        :reqjson string description: (*optional*) A helpful description of
                                     the Attribute
        :reqjson bool required: (*optional*) Whether this attribute should be required.
        :reqjson bool display: (*optional*) Whether this attribute should be be displayed
                               by default in UIs.
        :reqjson bool multi: (*optional*) Whether the attribute should be treated as a
                             list type.

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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            raise exc.NotFound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        try:
            description = self.jbody.get("description", "")
            required = self.jbody.get("required", False)
            display = self.jbody.get("display", False)
            multi = self.jbody.get("multi", False)
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute.update(
                self.current_user.id,
                description=description, required=required,
                display=display, multi=multi
            )
        except IntegrityError as err:
            raise exc.Conflict(str(err.orig))
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)

        self.success({
            "attribute": attribute.to_dict(),
        })

    @any_perm("admin")
    def delete(self, site_id, attribute_id):
        """ **Delete an Attribute**

        **Example Request**:

        .. sourcecode:: http

            DELETE /api/sites/1/attributes/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "message": Attribute 1 deleted."
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param attribute_id: ID of the Attribute being deleted.
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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()

        if not attribute:
            raise exc.NotFound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(
                    site_id, attribute_id
                )
            )

        try:
            attribute.delete(self.current_user.id)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)

        self.success({
            "message": "Attribute {} deleted from Site {}.".format(
                attribute_id, site_id
            ),
        })


class NetworksHandler(ApiHandler):

    @any_perm("admin")
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

            {
                "status": "ok",
                "data": {
                    "network": {
                        "id": 1,
                        "parent_id": null,
                        "site_id": 1,
                        "is_ip": false,
                        "ip_version": "4",
                        "network_address": "10.0.0.0",
                        "prefix_length": "8",
                        "attributes": {"vlan": "23"}
                    }
                }
            }

        :permissions: * **admin**

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
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        try:
            cidr = self.jbody["cidr"]
            attributes = self.jbody.get("attributes", {})
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            network = models.Network.create(
                self.session, self.current_user.id, site_id,
                cidr=cidr, attributes=attributes,
            )
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except (ValueError, exc.ValidationError) as err:
            raise exc.BadRequest(err.message)

        self.created("/api/sites/{}/networks/{}".format(site_id, network.id), {
            "network": network.to_dict(),
        })

    def get(self, site_id):
        """ **Get all Networks**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/networks HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "networks": [
                        {
                            "id": 1,
                            "parent_id": null,
                            "site_id": 1,
                            "is_ip": false,
                            "ip_version": "4",
                            "network_address": "10.0.0.0",
                            "prefix_length": "8",
                            "attributes": {}
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Networks from.
        :type site_id: int

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.
        :query bool root_only: (*optional*) Filter to root networks.
                               Default: false
        :query bool include_networks: (*optional*) Include non-IP networks.
                                      Default: true
        :query bool include_ips: (*optional*) Include IP addresses.
                                 Default: false

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        root_only = qpbool(self.get_argument("root_only", False))
        include_networks = qpbool(self.get_argument("include_networks", True))
        include_ips = qpbool(self.get_argument("include_ips", False))

        networks = site.networks(
            root=root_only, include_ips=include_ips,
            include_networks=include_networks
        )

        offset, limit = self.get_pagination_values()
        networks, total = self.paginate_query(networks, offset, limit)

        self.success({
            "networks": [network.to_dict() for network in networks],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class NetworkHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ **Get a specific Network**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/networks/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "network": {
                        "id": 1,
                        "parent_id": null,
                        "site_id": 1,
                        "is_ip": false,
                        "ip_version": "4",
                        "network_address": "10.0.0.0",
                        "prefix_length": "8",
                        "attributes": {}
                    }
                }
            }

        :param site_id: ID of the Site this Network is under.
        :type site_id: int

        :param network_id: ID of the Network being retrieved.
        :type network_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Network was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            raise exc.NotFound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        self.success({
            "network": network.to_dict(),
        })

    @any_perm("admin")
    def put(self, site_id, network_id):
        """ **Update a Network**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/sites/1/networks/1 HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "attributes": {"vlan": "4"}
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "network": {
                        "id": 1,
                        "parent_id": null,
                        "site_id": 1,
                        "is_ip": false,
                        "ip_version": "4",
                        "network_address": "10.0.0.0",
                        "prefix_length": "8",
                        "attributes": {"vlan": "4"}
                    }
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param network_id: ID of the Attribute being updated.
        :type network_id: int

        :reqjson object attributes: (*optional*) A key/value pair of attributes
                                    attached to the network

        :reqheader Content-Type: The server expects application/json.
        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or Network was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            raise exc.NotFound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        try:
            attributes = self.jbody.get("attributes", {})
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            network.update(self.current_user.id, attributes=attributes)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)

        self.success({
            "network": network.to_dict(),
        })

    @any_perm("admin")
    def delete(self, site_id, network_id):
        """ **Delete a Network**

        **Example Request**:

        .. sourcecode:: http

            DELETE /api/sites/1/networks/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "message": Network 1 deleted."
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param network_id: ID of the Network being deleted.
        :type network_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or Attribute was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            raise exc.NotFound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        try:
            network.delete(self.current_user.id)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)

        self.success({
            "message": "Network {} deleted from Site {}.".format(
                network_id, site_id
            ),
        })

class NetworkSubnetsHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ **Get subnets of a Network**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/networks/1/subnets HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "networks": [
                        {
                            "id": 2,
                            "parent_id": 1,
                            "site_id": 1,
                            "is_ip": false,
                            "ip_version": "4",
                            "network_address": "10.0.0.0",
                            "prefix_length": "24",
                            "attributes": {}
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Networks from.
        :type site_id: int

        :param network_id: ID of the Network we're requesting subnets from.
        :type network_id: int

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.
        :query bool direct: (*optional*) Return only direct subnets.
                            Default: false
        :query bool include_networks: (*optional*) Include non-IP networks.
                                      Default: true
        :query bool include_ips: (*optional*) Include IP addresses.
                                 Default: false

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Network was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            raise exc.NotFound(
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

        offset, limit = self.get_pagination_values()
        networks, total = self.paginate_query(networks, offset, limit)

        self.success({
            "networks": [network.to_dict() for network in networks],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class NetworkSupernetsHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ **Get supernets of a Network**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/networks/2/supernets HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "networks": [
                        {
                            "id": 1,
                            "parent_id": null,
                            "site_id": 1,
                            "is_ip": false,
                            "ip_version": "4",
                            "network_address": "10.0.0.0",
                            "prefix_length": "8",
                            "attributes": {}
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Networks from.
        :type site_id: int

        :param network_id: ID of the Network we're requesting supernets from.
        :type network_id: int

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.
        :query bool direct: (*optional*) Return only direct supernets.
                            Default: false

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Network was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        network = self.session.query(models.Network).filter_by(
            id=network_id,
            site_id=site_id
        ).scalar()

        if not network:
            raise exc.NotFound(
                "No such Network found at (site_id, id) = ({}, {})".format(
                    site_id, network_id
                )
            )

        direct = qpbool(self.get_argument("direct", False))

        networks = network.supernets(self.session, direct=direct)

        offset, limit = self.get_pagination_values()
        networks, total = self.paginate_query(networks, offset, limit)

        self.success({
            "networks": [network.to_dict() for network in networks],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class ChangesHandler(ApiHandler):
    def get(self, site_id):
        """ **Get all Changes**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/changes HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "changes": [
                        {
                            "id": 1,
                            "site": {
                                "id": 1,
                                "name": "Site 1",
                                "description": ""
                            },
                            "user": {
                                "id": 1,
                                "email": "user@localhost"
                            },
                            "change_at": 1420062748,
                            "event": "Create",
                            "resource_name": "Site",
                            "resource_id": 1,
                            "resource": {
                                "name": "New Site",
                                "description": ""
                            },
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Changes from.
        :type site_id: int

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.
        :query string event: (*optional*) Filter result to specific event.
                             Default: false
        :query string resource_name: (*optional*) Filter result to specific
                                     resource type. Default: false
        :query string resource_id: (*optional*) Filter result to specific resource id.
                                   Requires: resource_name, Default: false

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: Invalid query parameter values.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """

        event = self.get_argument("event", None)
        if event is not None and event not in models.CHANGE_EVENTS:
            raise exc.BadRequest("Invalid event.")

        resource_name = self.get_argument("resource_name", None)
        if resource_name is not None and resource_name not in models.RESOURCE_BY_NAME:
            raise exc.BadRequest("Invalid resource type.")

        resource_id = self.get_argument("resource_id", None)
        if resource_id is not None and resource_name is None:
            raise exc.BadRequest("resource_id requires resource_name to be set.")

        changes = self.session.query(models.Change)

        if site_id is not None:
            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                raise exc.NotFound("No such Site found at id {}".format(site_id))
            changes = changes.filter_by(site_id=site_id)

        if event is not None:
            changes = changes.filter_by(event=event)

        if resource_name is not None:
            changes = changes.filter_by(resource_name=resource_name)

        if resource_id is not None:
            changes = changes.filter_by(resource_id=resource_id)

        changes = changes.order_by(desc("change_at"))

        offset, limit = self.get_pagination_values()
        changes, total = self.paginate_query(changes, offset, limit)

        self.success({
            "changes": [change.to_dict() for change in changes],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class ChangeHandler(ApiHandler):
    def get(self, site_id, change_id):
        """ **Get a specific Change**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/changes/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "change": {
                        "id": 1,
                        "site": {
                            "id": 1,
                            "name": "Site 1",
                            "description": ""
                        },
                        "user": {
                            "id": 1,
                            "email": "user@localhost"
                        },
                        "change_at": 1420062748,
                        "event": "Create",
                        "resource_name": "Site",
                        "resource_id": 1,
                        "resource": {
                            "name": "New Site",
                            "description": ""
                        },
                    }
                }
            }

        :param site_id: ID of the Site to retrieve Changes from.
        :type site_id: int
        :param change_id: ID of the Change.
        :type change_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site/Change was not found.
        """

        change = self.session.query(models.Change).filter_by(
            id=change_id, site_id=site_id
        ).scalar()

        if not change:
            raise exc.NotFound(
                "No such Change ({}) at Site ({})".format(change_id, site_id)
            )

        self.success({
            "change": change.to_dict(),
        })

class UsersHandler(ApiHandler):
    def get(self):
        """ **Get all Users**

        **Example Request**:

        .. sourcecode:: http

            GET /api/users HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "users": [
                        {
                            "id": 1
                            "email": "user@localhost"
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :reqheader X-NSoT-Email: required for all api requests.

        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        """

        users = self.session.query(models.User)

        offset, limit = self.get_pagination_values()
        users, total = self.paginate_query(users, offset, limit)

        self.success({
            "users": [user.to_dict() for user in users],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class UserHandler(ApiHandler):
    def get(self, user_id):
        """ **Get a specific User**

        **Example Request**:

        .. sourcecode:: http

            GET /api/users/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "user": {
                        "id": 1
                        "email": "user@localhost"
                        "permissions": {
                            1: {
                                "user_id": 1,
                                "site_id": 1,
                                "permissions": ["admin"]
                            }
                        }
                    }
                }
            }

        :param user_id: ID of the User to retrieve or 0 for self.
        :type user_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """

        if user_id == "0":
            user = self.current_user
        else:
            user = self.session.query(models.User).filter_by(
                id=user_id,
            ).scalar()

        if not user:
            raise exc.NotFound(
                "No such User found at (id) = ({})".format(user_id)
            )

        self.success({
            "user": user.to_dict(with_permissions=True),
        })

class UserPermissionsHandler(ApiHandler):
    def get(self, user_id):
        """ **Get permissions for a specific User**

        **Example Request**:

        .. sourcecode:: http

            GET /api/users/1/permissions HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "permissions": {
                        1: {
                            "user_id": 1,
                            "site_id": 1,
                            "permissions": ["admin"]
                        }
                    }
                }
            }

        :param user_id: ID of the User to retrieve or 0 for self.
        :type user_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The User was not found.
        """

        if user_id == "0":
            user = self.current_user
        else:
            user = self.session.query(models.User).filter_by(
                id=user_id,
            ).scalar()

        if not user:
            raise exc.NotFound(
                "No such User found at (id) = ({})".format(user_id)
            )

        permissions = self.session.query(models.Permission).filter_by(
            user_id=user.id
        )

        self.success({
            "permissions": user.get_permissions(),
        })

class UserPermissionHandler(ApiHandler):
    def get(self, user_id, site_id):
        """ **Get permissions for a specific User and Site**

        **Example Request**:

        .. sourcecode:: http

            GET /api/users/1/permissions/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "permission": {
                        "user_id": 1,
                        "site_id": 1,
                        "permissions": ["admin"]
                    }
                }
            }

        :param user_id: ID of the User or 0 for self.
        :type user_id: int

        :param site_id: ID of the Site
        :type site_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The User or Site was not found.
        """

        if user_id == "0":
            user = self.current_user
        else:
            user = self.session.query(models.User).filter_by(
                id=user_id,
            ).scalar()
        if not user:
            raise exc.NotFound("No such User found at (id) = ({})".format(user_id))

        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        permission = self.session.query(models.Permission).filter_by(
            user_id=user.id, site_id=site_id
        ).scalar()

        if not permission:
            raise exc.NotFound(
                "No such Permission found at (user_id, site_id) = ({})".format(
                    user.id, site_id
                )
            )

        self.success({
            "permission": permission.to_dict(),
        })

    @any_perm("admin")
    def put(self, user_id, site_id):
        """ **Create/Update a Users Permissions for a Site**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/users/2/permissions/1 HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "permissions": ["networks"]
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "permission": {
                        "user_id": 2,
                        "site_id": 1,
                        "permissions": ["networks"]
                    }
                }
            }

        :permissions: * **admin**

        :param user_id: ID of the User
        :type user_id: int

        :param site_id: ID of the Site
        :type site_id: int

        :reqjson array permissions: A list of permissions the user should have.

        :reqheader Content-Type: The server expects application/json.
        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or User was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        permission = self.session.query(models.Permission).filter_by(
                user_id=user_id, site_id=site_id
        ).scalar()

        # If the permission exists it's safe to assume the user/site exists. If not
        # we're adding a new permission so verify that the user/site are valid.
        if not permission:
            user = self.session.query(models.User).filter_by(id=user_id).scalar()
            if not user:
                raise exc.NotFound("No such User found at (id) = ({})".format(user_id))

            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                raise exc.NotFound("No such Site found at id {}".format(site_id))

        try:
            permissions = self.jbody["permissions"]
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

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
            raise exc.Conflict(str(err.orig))

        self.success({
            "permission": permission.to_dict(),
        })


class NotFoundHandler(ApiHandler):
    def get(self):
        raise exc.NotFound("Endpoint not found")
