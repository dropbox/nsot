from sqlalchemy.exc import IntegrityError


from .util import ApiHandler
from .. import exc
from .. import models
from ..util import qp_to_bool as qpbool


class SitesHandler(ApiHandler):

    def post(self):
        """ Create a new Site."""

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description", "")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

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
        """ Return all Sites."""
        sites = self.session.query(models.Site).all()
        self.success({
            "sites": [site.to_dict() for site in sites],
        })


class SiteHandler(ApiHandler):
    def get(self, site_id):
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))
        self.success({
            "site": site.to_dict(),
        })

    def put(self, site_id):
        site = self.session.query(models.Site).filter_by(id=site_id).scalar()
        if not site:
            return self.notfound("No such Site found at id {}".format(site_id))

        try:
            name = self.jbody["name"]
            description = self.jbody.get("description", "")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            site.name = name
            site.description = description
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.success({
            "site": site.to_dict(),
        })

    def delete(self, site_id):
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

    def post(self, site_id):
        """ Create a new NetworkAttribute."""

        try:
            name = self.jbody["name"]
            required = self.jbody.get("required")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute = models.NetworkAttribute.create(
                self.session, self.current_user.id,
                site_id=site_id, name=name, required=qpbool(required)
            )
        except IntegrityError as err:
            return self.conflict(str(err.orig))
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.created("/api/sites/{}/network_attributes/{}".format(
            site_id, attribute.id
        ))

    def get(self, site_id):
        """ Return all NetworkAttributes."""

        required = qpbool(self.get_argument("required", None))

        attributes = self.session.query(models.NetworkAttribute).filter_by(
            site_id=site_id
        )

        if required:
            attributes = attributes.filter_by(required==True)

        self.success({
            "network_attributes": [attribute.to_dict() for attribute in attributes],
        })


class NetworkAttributeHandler(ApiHandler):
    def get(self, site_id, attribute_id):
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

    def put(self, site_id, attribute_id):
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
            name = self.jbody["name"]
            required = self.jbody.get("required")
        except KeyError as err:
            return self.badrequest("Missing Required Argument: {}".format(err.message))

        try:
            attribute.name = name
            attribute.required = qpbool(required)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.success({
            "network_attribute": attribute.to_dict(),
        })

    def delete(self, site_id, attribute_id):
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


class NetworkAttributeNetworksHandler(ApiHandler):
    def get(self, site_id, attribute_id):
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

        #TODO(gary): do.
        networks = []

        self.success({
            "networks": networks
        })

class NetworksHandler(ApiHandler):

    def post(self, site_id):
        """ Create a new Network."""

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

        self.created("/api/networks/{}".format(network.id))

    def get(self, site_id):
        """ Return all Networks. """

        root_only = qpbool(self.get_argument("root_only", False))
        include_networks = qpbool(self.get_argument("include_networks", True))
        include_ips = qpbool(self.get_argument("include_ips", False))

        networks = models.Network.networks(
            self.session, root=root_only,
            include_ips=include_ips, include_networks=include_networks
        )

        self.success({
            "networks": [network.to_dict() for network in networks],
        })


class NetworkHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return a specific Network. """

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

    def put(self, site_id, network_id):
        """ Update a Network. """

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
            network.set_attributes(attributes)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(err.orig.message)
        except exc.ValidationError as err:
            return self.badrequest(err.message)

        self.success({
            "network": network.to_dict(),
        })

    def delete(self, site_id, network_id):
        """ Delete a Network. """

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

        resource_id = self.get_arguement("resource_id", None)
        if resource_id is not None and resource_type is None:
            return self.badrequest("resource_id requires resource_type to be set.")

        changes = self.session.query(models.Change)

        if site_id is not None:
            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                return self.notfound("No such Site found at id {}".format(site_id))
            changes = changes.filter_by(site_id=site_id)

        if event is not None:
            changes = change.filter_by(event=event)

        if resource_type is not None:
            changes = change.filter_by(resource_type=resource_type)

        if resource_id is not None:
            changes = change.filter_by(resource_id=resource_id)


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

class NotFoundHandler(ApiHandler):
    def get(self):
        return self.notfound("Endpoint not found")
