import ipaddress
import logging
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError


from .util import ApiHandler
from .. import exc
from ..decorators import any_perm
from .. import models
from ..util import qp_to_bool as qpbool, parse_set_query


log = logging.getLogger(__name__)


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
        """ **Create an Attribute or collection of Attributes**

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

        You may also create a collection of objects by submitting them as a list
        inside of a dictionary with an ``attributes`` key.

        **Example collection request**:

        .. sourcecode:: http

            POST /api/sites/1/attributes HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "attributes": [
                    {
                        "name": "owner",
                        "resource_name": "Network",
                    },
                    {
                        "name": "metro",
                        "resource_name": "Network",
                    }
                ]
            }

        **Example collection response**:

        Note that when creating a collection the response will not contain a
        ``Location`` header.

        .. sourcecode:: http

            HTTP/1.1 201 OK

            {
                "status": "ok",
                "data": {
                    "attributes": [
                        {
                            "id": 1,
                            "name": "owner",
                            "resource_name": "Network",
                            "required": false,
                            "display": false,
                            "multi": false,
                            "constraints": {
                                "allow_empty": false,
                                "pattern": "",
                                "valid_values": []
                            }
                        },
                        {
                            "id": 2,
                            "name": "metro",
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
                    "total": 2
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

        # Fetch collection from the body or the body itself
        objects = self.jbody.get('attributes', [self.jbody])

        attributes = []
        for obj in objects:
            try:
                name = obj["name"]
                description = obj.get("description")
                resource_name = obj["resource_name"]
                required = obj.get("required", False)
                display = obj.get("display", False)
                multi = obj.get("multi", False)
                constraints = obj.get("constraints", {})
            except KeyError as err:
                raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

            attribute = self.create_object(
                site_id, name, description, resource_name, required, display,
                multi, constraints, commit=False
            )
            attributes.append(attribute.to_dict())
        else:
            self.session.commit()

        # Return a collection w/ no Location header
        if len(attributes) > 1:
            self.created(
                data={"attributes": attributes, "total": len(attributes)}
            )
        # Or return a single object
        else:
            attribute = attributes[0]
            uri = "/api/sites/{}/attributes/{}".format(site_id, attribute['id'])
            self.created(uri, {"attribute": attribute})

    def create_object(self, site_id, name, description, resource_name, required,
                      display, multi, constraints, commit=True):
        """Create an Attribute object."""
        site_id = int(site_id)
        try:
            attribute = models.Attribute.create(
                self.session, self.current_user.id,
                site_id=site_id, name=name, description=description,
                resource_name=resource_name, required=required, display=display,
                multi=multi, constraints=constraints, commit=commit
            )
        except IntegrityError as err:
            raise exc.Conflict(str(err.orig))
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)
        return attribute

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
        :query string resource_name: (*optional*) Filter to attributes for a specific resource.
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
            constraints = self.jbody.get("constraints", {})
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute.update(
                self.current_user.id,
                description=description, required=required,
                display=display, multi=multi, constraints=constraints
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


class DevicesHandler(ApiHandler):

    @any_perm("admin")
    def post(self, site_id):
        """ **Create a Device or collection of Devices**

        **Example Request**:

        .. sourcecode:: http

            POST /api/sites/1/devices HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "hostname": "foobarhost",
                "attributes": {
                    "owner": "network-tools"
                }
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 201 OK
            Location: /api/sites/1/devices/1

            {
                "status": "ok",
                "data": {
                    "device": {
                        "id": 1,
                        "site_id": 1,
                        "hostname": "foobarhost",
                        "attributes": {"owner": "network-tools"}
                    }
                }
            }

        You may also create a collection of objects by submitting them as a list
        inside of a dictionary with an ``devices`` key.

        **Example collection request**:

        .. sourcecode:: http

            POST /api/sites/1/devices HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "devices": [
                    {"hostname": "foobarhost1"},
                    {"hostname": "foobarhost2"}
                ]
            }

        **Example collection response**:

        Note that when creating a collection the response will not contain a
        ``Location`` header.

        .. sourcecode:: http

            HTTP/1.1 201 OK

            {
                "status": "ok",
                "data": {
                    "devices": [
                        {
                            "id": 1,
                            "hostname": "foobarhost1",
                            "site_id": 1,
                            "attributes": {}
                        },
                        {
                            "id": 2,
                            "hostname": "foobarhost2",
                            "site_id": 1,
                            "attributes": {}
                        }
                    ],
                    "total": 2
                }
            }

        :permissions: * **admin**

        :param site_id: ID of the Site where this should be created.
        :type site_id: int

        :reqjson string hostname: The hostname of the network device.
        :reqjson object attributes: (*optional*) An object of key/value pairs
                                    attached to this device.

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

        # Fetch collection from the body or the body itself as a list.
        objects = self.jbody.get('devices', [self.jbody])

        devices = []
        for obj in objects:
            try:
                hostname = obj["hostname"]
                attributes = obj.get("attributes", {})
            except KeyError as err:
                raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

            device = self.create_object(
                site_id, hostname, attributes, commit=False
            )
            devices.append(device.to_dict())
        else:
            self.session.commit()

        # Return a collection w/ no Location header
        if len(devices) > 1:
            self.created(data={"devices": devices, "total": len(devices)})
        # Or return a single object
        else:
            device = devices[0]
            uri = "/api/sites/{}/devices/{}".format(site_id, device['id'])
            self.created(uri, {"device": device})

    def create_object(self, site_id, hostname, attributes, commit=True):
        """Create a Device object."""
        site_id = int(site_id)
        try:
            device = models.Device.create(
                self.session, self.current_user.id, site_id=site_id,
                hostname=hostname, attributes=attributes, commit=commit
            )
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except (ValueError, exc.ValidationError) as err:
            raise exc.BadRequest(err.message)
        return device

    def get(self, site_id):
        """ **Get all Devices**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/devices HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "devices": [
                        {
                            "id": 1,
                            "site_id": 1,
                            "hostname": "foobarhost",
                            "attributes": {"owner": "network-tools"}
                        }
                    ],
                    "limit": null,
                    "offset": 0,
                    "total": 1,
                }
            }

        :param site_id: ID of the Site to retrieve Devices from.
        :type site_id: int

        :query string hostname:
            (*optional*) Filter to device with hostname
        :query string attributes:
            (*optional*) Filter to device with matching attribute in k=v
            format. Can be supplied multiple times.
        :query int limit: (*optional*) Limit result to N resources.
        :query int offset: (*optional*) Skip the first N resources.

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        devices = site.devices()

        hostname = self.get_argument("hostname", None)
        attributes = self.get_arguments("attributes", [])

        if hostname is not None:
            devices = devices.filter_by(hostname=hostname)

        # Just iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        for attribute in attributes:
            key, _, val = attribute.partition('=')
            next_set = site.devices(key, val)
            devices = devices.filter(
                models.Device.id.in_(
                    next_set.with_entities(models.Device.id)
                )
            )

        offset, limit = self.get_pagination_values()
        devices, total = self.paginate_query(devices, offset, limit)

        self.success({
            "devices": [device.to_dict() for device in devices],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class DevicesQueryHandler(ApiHandler):
    """
    Use set operations syntax to perform queries for Devices.
    """
    def get(self, site_id):
        """
        **Intersection request**:

        .. sourcecode:: http

            GET /api/sites/1/devices/query?query=foo%3Dbar HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Intersection response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "devices": [
                        {
                            "attributes": {
                                "owner": "team-networking",
                                "foo": "bar"
                            },
                            "hostname": "foo-bar1",
                            "site_id": 1,
                            "id": 1
                        },
                        {
                            "attributes": {
                                "owner": "jathan",
                                "foo": "bar"
                            },
                            "hostname": "foo-bar3",
                            "site_id": 1,
                            "id": 3
                        }
                    ]
                }
            }

        **Difference request**:

        .. sourcecode:: http

            GET /api/sites/1/devices/query?query=foo%3Dbar+-owner%3Djathan HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Difference response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "devices": [
                        {
                            "attributes": {
                                "owner": "team-networking",
                                "foo": "bar"
                            },
                            "hostname": "foo-bar1",
                            "site_id": 1,
                            "id": 1
                        }
                    ]
                }
            }

        :param site_id: ID of the Site to retrieve Devices from.
        :type site_id: int

        :param query: Set query representation
        :type query: str

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site at site_id was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        query = self.get_argument("query", "")

        # Try to convert attributes into a dict.
        try:
            attributes = parse_set_query(query)
        except (ValueError, TypeError):
            attributes = []

        devices = site.devices()

        # Iterate a/v pairs and combine query results using MySQL-compatible set
        # operations w/ the ORM
        for action, name, value in attributes:
            next_set = site.devices(attribute_name=name, attribute_value=value)

            # This is the MySQL-compatible manual implementation
            if action == 'union':
                log.debug('SQL UNION')
                devices = devices.union(next_set)
            elif action == 'difference':
                log.debug('SQL DIFFERENCE')
                devices = devices.filter(
                    models.Device.id.notin_(
                        next_set.with_entities(models.Device.id)
                    )
                )
            elif action == 'intersection':
                log.debug('SQL INTERSECTION')
                devices = devices.filter(
                    models.Device.id.in_(
                        next_set.with_entities(models.Device.id)
                    )
                )
            else:
                raise exc.BadRequest('BAD SET QUERY: %r' % (action,))

        # Always order the objects by ID
        devices = devices.order_by(models.Device.id)

        offset, limit = self.get_pagination_values()
        devices, total = self.paginate_query(devices, offset, limit)

        self.success({
            "devices": [device.to_dict() for device in devices],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class DeviceHandler(ApiHandler):
    def get(self, site_id, device_id):
        """ **Get a specific Device**

        **Example Request**:

        .. sourcecode:: http

            GET /api/sites/1/devices/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "device": {
                        "id": 1,
                        "site_id": 1,
                        "hostname": "foobarhost",
                        "attributes": {"owner": "network-tools"}
                    }
                }
            }

        :param site_id: ID of the Site this Device is under.
        :type site_id: int

        :param device_id: ID of the Device being retrieved.
        :type device_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 404: The Site or Device was not found.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        device = self.session.query(models.Device).filter_by(
            id=device_id,
            site_id=site_id
        ).scalar()

        if not device:
            raise exc.NotFound(
                "No such Device found at (site_id, id) = ({}, {})".format(
                    site_id, device_id
                )
            )

        self.success({
            "device": device.to_dict(),
        })

    @any_perm("admin")
    def put(self, site_id, device_id):
        """ **Update a Device**

        **Example Request**:

        .. sourcecode:: http

            PUT /api/sites/1/devices/1 HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "hostname": "foobarhost",
                "attributes": {"owner": "network-eng"}
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "device": {
                        "id": 1,
                        "site_id": 1,
                        "hostname": "foobarhost",
                        "attributes": {"owner": "network-eng"}
                    }
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param device_id: ID of the Attribute being updated.
        :type device_id: int

        :reqjson string hostname: The hostname of the device.
        :reqjson object attributes: (*optional*) A key/value pair of attributes
                                    attached to the device

        :reqheader Content-Type: The server expects application/json.
        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 400: The request was malformed.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The Site or Device was not found.
        :statuscode 409: There was a conflict with another resource.
        """
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            raise exc.NotFound("No such Site found at id {}".format(site_id))

        device = self.session.query(models.Device).filter_by(
            id=device_id,
            site_id=site_id
        ).scalar()

        if not device:
            raise exc.NotFound(
                "No such Device found at (site_id, id) = ({}, {})".format(
                    site_id, device_id
                )
            )

        try:
            hostname = self.jbody["hostname"]
            attributes = self.jbody.get("attributes", {})
        except KeyError as err:
            raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

        try:
            device.update(self.current_user.id, hostname=hostname, attributes=attributes)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except exc.ValidationError as err:
            raise exc.BadRequest(err.message)

        self.success({
            "device": device.to_dict(),
        })

    @any_perm("admin")
    def delete(self, site_id, device_id):
        """ **Delete a Device**

        **Example Request**:

        .. sourcecode:: http

            DELETE /api/sites/1/devices/1 HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "message": Device 1 deleted."
                }
            }


        :permissions: * **admin**

        :param site_id: ID of the Site that should be updated.
        :type site_id: int

        :param device_id: ID of the Device being deleted.
        :type device_id: int

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

        device = self.session.query(models.Device).filter_by(
            id=device_id,
            site_id=site_id
        ).scalar()

        if not device:
            raise exc.NotFound(
                "No such Device found at (site_id, id) = ({}, {})".format(
                    site_id, device_id
                )
            )

        try:
            device.delete(self.current_user.id)
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)

        self.success({
            "message": "Device {} deleted from Site {}.".format(
                device_id, site_id
            ),
        })


class NetworksHandler(ApiHandler):

    @any_perm("admin")
    def post(self, site_id):
        """ **Create a Network or collection of Networks**

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

        You may also create a collection of objects by submitting them as a list
        inside of a dictionary with an ``networks`` key.

        **Example collection request**:

        .. sourcecode:: http

            POST /api/sites/1/networks HTTP/1.1
            Host: localhost
            Content-Type: application/json
            X-NSoT-Email: user@localhost

            {
                "networks": [
                    {"cidr": "10.0.0.0/8"},
                    {"cidr": "172.16.0.0/12"}
                ]
            }

        **Example collection response**:

        Note that when creating a collection the response will not contain a
        ``Location`` header.

        .. sourcecode:: http

            HTTP/1.1 201 OK

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
                        },
                        {
                            "id": 2,
                            "parent_id": null,
                            "site_id": 1,
                            "is_ip": false,
                            "ip_version": "4",
                            "network_address": "172.16.0.0",
                            "prefix_length": "12",
                            "attributes": {}
                        }
                    ],
                    "total": 2
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

        # Fetch collection from the body or the body itself
        objects = self.jbody.get('networks', [self.jbody])

        networks = []
        for obj in objects:
            try:
                cidr = obj["cidr"]
                attributes = obj.get("attributes", {})
            except KeyError as err:
                raise exc.BadRequest("Missing Required Argument: {}".format(err.message))

            network = self.create_object(
                site_id, cidr, attributes, commit=False
            )
            networks.append(network.to_dict())
        else:
            self.session.commit()

        # Return a collection w/ no Location header
        if len(networks) > 1:
            self.created(data={"networks": networks, "total": len(networks)})
        # Or return a single object
        else:
            network = networks[0]
            uri = "/api/sites/{}/networks/{}".format(site_id, network['id'])
            self.created(uri, {"network": network})

    def create_object(self, site_id, cidr, attributes, commit=True):
        """Create a Network object."""
        site_id = int(site_id)
        try:
            network = models.Network.create(
                self.session, self.current_user.id, site_id,
                cidr=cidr, attributes=attributes,
            )
        except IntegrityError as err:
            raise exc.Conflict(err.orig.message)
        except (ValueError, exc.ValidationError) as err:
            raise exc.BadRequest(err.message)
        return network

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
        :query string network_address:
            (*optional*) Filter to networks matching this network address
        :query int prefix_length:
            (*optional*) Filter to networks matching this prefix length
        :query string cidr:
            (*optional*) Filter to networks matching this CIDR. If provided,
            this overrides ``network_address`` and ``prefix_length``
        :query string attributes:
            (*optional*) Filter to device with matching attribute in k=v

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

        # Filters for address/prefix/attributes
        cidr = self.get_argument("cidr", None)
        attributes = self.get_arguments("attributes", [])
        network_address = self.get_argument("network_address", None)
        prefix_length = self.get_argument("prefix_length", None)

        # If cidr is provided, use it to populate network_address and prefix_length
        if cidr is not None:
            log.debug('got cidr: %s' % cidr)
            network_address, _, prefix_length = cidr.partition('/')
        # If network_address is provided, pack it.
        if network_address is not None:
            log.debug('got network_address: %s' % network_address)
            network_address = ipaddress.ip_address(network_address).packed
            networks = networks.filter_by(network_address=network_address)
        # If prefix_length is provided, convert it to an int.
        if prefix_length is not None:
            log.debug('got prefix_length: %s' % prefix_length)
            try:
                prefix_length = int(prefix_length)
            except ValueError:
                raise ValueError('Invalid prefix_length: %s' % prefix_length)
            networks = networks.filter_by(prefix_length=prefix_length)

        # Iterate the attributes and try to look them up as if they are k=v
        # and naively do an intersection query.
        for attribute in attributes:
            key, _, val = attribute.partition('=')
            # Retrieve next set of networks using the same arguments as the
            # initial query.
            next_set = site.networks(
                attribute_name=key, attribute_value=val, root=root_only,
                include_ips=include_ips, include_networks=include_networks
            )
            networks = networks.filter(
                models.Network.id.in_(
                    next_set.with_entities(models.Network.id)
                )
            )

        offset, limit = self.get_pagination_values()
        networks, total = self.paginate_query(networks, offset, limit)

        self.success({
            "networks": [network.to_dict() for network in networks],
            "limit": limit,
            "offset": offset,
            "total": total,
        })


class NetworksQueryHandler(ApiHandler):
    """
    Use set operations syntax to perform queries for Networks.
    """
    def get(self, site_id):
        """
        **Intersection request**:

        .. sourcecode:: http

            GET /api/sites/1/networks/query?query=owner%3Djathan HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Intersection response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "networks": [
                        {
                            "is_ip": false,
                            "site_id": 1,
                            "network_address": "10.0.0.0",
                            "parent_id": null,
                            "prefix_length": 8,
                            "ip_version": "4",
                            "attributes": {
                                "owner": "jathan",
                                "cluster": ""
                            },
                            "id": 1
                        },
                        {
                            "is_ip": false,
                            "site_id": 1,
                            "network_address": "10.20.30.0",
                            "parent_id": 1,
                            "prefix_length": 24,
                            "ip_version": "4",
                            "attributes": {
                                "owner": "jathan",
                                "foo": "bar"
                            },
                            "id": 4
                        }
                    ]
                }
            }

        **Difference request**:

        .. sourcecode:: http

            GET /api/sites/1/networks/query?query=owner%3Djathan+-foo%3Dbar HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Difference response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "networks": [
                        {
                            "is_ip": false,
                            "site_id": 1,
                            "network_address": "10.0.0.0",
                            "parent_id": null,
                            "prefix_length": 8,
                            "ip_version": "4",
                            "attributes": {
                                "owner": "jathan",
                                "cluster": ""
                            },
                            "id": 1
                        }
                    ]
                }
            }

        :param site_id: ID of the Site to retrieve Devices from.
        :type site_id: int

        :param query: Set query representation
        :type query: str

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

        query = self.get_argument("query", "")
        root_only = qpbool(self.get_argument("root_only", False))
        include_networks = qpbool(self.get_argument("include_networks", True))
        include_ips = qpbool(self.get_argument("include_ips", False))

        # Try to convert attributes into a dict.
        try:
            attributes = parse_set_query(query)
        except (ValueError, TypeError):
            attributes = []

        networks = site.networks(
            root=root_only, include_ips=include_ips,
            include_networks=include_networks
        )

        # Iterate a/v pairs and combine query results using MySQL-compatible set
        # operations w/ the ORM
        for action, name, value in attributes:
            next_set = site.networks(
                attribute_name=name, attribute_value=value, root=root_only,
                include_ips=include_ips, include_networks=include_networks
            )

            # This is the MySQL-compatible manual implementation
            if action == 'union':
                log.debug('SQL UNION')
                networks = networks.union(next_set)
            elif action == 'difference':
                log.debug('SQL DIFFERENCE')
                networks = networks.filter(
                    models.Network.id.notin_(
                        next_set.with_entities(models.Network.id)
                    )
                )
            elif action == 'intersection':
                log.debug('SQL INTERSECTION')
                networks = networks.filter(
                    models.Network.id.in_(
                        next_set.with_entities(models.Network.id)
                    )
                )
            else:
                raise exc.BadRequest('BAD SET QUERY: %r' % (action,))

        # Always order the objects by ID
        networks = networks.order_by(models.Network.id)

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


class AuthTokenLoginHandler(ApiHandler):
    """Used to authenticate users and return an auth_token."""

    def get_current_user(self):
        try:
            email = self.jbody['email']
            secret_key = self.jbody['secret_key']
        except KeyError as err:
            raise exc.Unauthorized('Missing required field: {}'.format(err.message))

        user = self.session.query(models.User).filter_by(email=email).scalar()

        # Make sure we've got a user and the secret_key is valid
        if user is not None and user.verify_secret_key(secret_key):
            return user  # Auth success

        raise exc.Unauthorized('Invalid email/secret_key')

    def post(self):
        """
        **Obtain an auth_token used for API calls.**

        **Example Request**:

        .. sourcecode:: http

            POST /api/authenticate HTTP/1.1
            Host: localhost
            Content-Type: application/json

            {
                "email": "user@localhost",
                "secret_key": "RmjJASeWQDHIoP7LMpSKGkofkoXnhbiBqauCnCR_InI=",
            }

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "auth_token": "gAAAAAbu5=="
                }
            }

        :reqjson string email: User's email address
        :reqjson string secret_key: Secret key for the user

        :reqheader Content-Type: The server expects a json body specified with
                                 this header.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without valid credentials.
        """
        user = self.get_current_user()

        # Return the auth_token
        self.success({
            'auth_token': user.generate_auth_token()
        })


class AuthTokenVerifyHandler(ApiHandler):
    """Used to verify an auth_token."""
    def post(self):
        """
        **Verify an auth_token.**

        **Example Request**:

        .. sourcecode:: http

            POST /api/verify_token HTTP/1.1
            Host: localhost
            Content-Type: application/json
            Authorization: AuthToken user@localhost:gAAAAAbu5==

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": true
            }

        :reqheader Authorization: required for all api requests.
        :reqheader Content-Type: The server expects a json body specified with
                                 this header.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without valid credentials.
        """
        user = self.get_current_user()

        # Return 'ok'
        self.success(True)


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

        :query bool with_secret_key: (*optional*) Include security_key
                                     (Self only.)

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
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

        user_kwargs = {
            "with_permissions": True,
        }

        with_secret_key = self.get_argument("with_secret_key", None)
        if with_secret_key is not None:
            if user != self.current_user:
                raise exc.Forbidden("Can't access secret_key of user that isn't you.")
            user_kwargs["with_secret_key"] = qpbool(with_secret_key)

        self.success({
            "user": user.to_dict(**user_kwargs),
        })


class UserRotateSecretKeyHandler(ApiHandler):
    def post(self, user_id):
        """ **Get a specific User**

        **Example Request**:

        .. sourcecode:: http

            POST /api/users/1/rotate_secret_key HTTP/1.1
            Host: localhost
            X-NSoT-Email: user@localhost

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "ok",
                "data": {
                    "secret_key": "k4ljk2345kl2j5k2fffml23",
                }
            }

        :param user_id: ID of the User to rotate key for or 0 for self.
        :type user_id: int

        :reqheader X-NSoT-Email: required for all api requests.

        :statuscode 200: The request was successful.
        :statuscode 401: The request was made without being logged in.
        :statuscode 403: The request was made with insufficient permissions.
        :statuscode 404: The User was not found.
        """

        if user_id == "0":
            user = self.current_user
        else:
            user = self.session.query(models.User).filter_by(
                id=user_id,
            ).scalar()

        if user != self.current_user:
            raise exc.Forbidden("Can't access secret_key of user that isn't you.")

        if not user:
            raise exc.NotFound(
                "No such User found at (id) = ({})".format(user_id)
            )

        user.rotate_secret_key()
        self.session.commit()

        self.success({
            "secret_key": user.secret_key,
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
