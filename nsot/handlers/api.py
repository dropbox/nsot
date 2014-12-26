from sqlalchemy.exc import IntegrityError

from .. import constants
from .. import exc
from .. import models
from .. import util

from .util import ApiHandler


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
        except ValidationError as err:
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

        self.session.delete(site)
        self.session.commit()

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

        if not constants.ATTRIBUTE_NAME.match(name):
            return self.badrequest("Invalid name parameter.")

        try:
            attribute = models.NetworkAttribute.create(
                session, current_user.id,
                site_id=site_id, name=name, required=util.qp_to_bool(required)
            )
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.created("/api/sites/{}/network_attributes/{}".format(
            site_id, attribute.id
        ))

    def get(self, site_id):
        """ Return all NetworkAttributes."""
        attributes = self.session.query(models.NetworkAttribute).filter_by(
            site_id=site_id
        ).all()
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

        if not constants.ATTRIBUTE_NAME.match(name):
            return self.badrequest("Invalid name parameter.")

        try:
            attribute.name = name
            attribute.required = util.qp_to_bool(required)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))

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

        # TODO(gary): Remove all references to this attribute or fail via
        # ON DELETE RESTRICT
        self.session.delete(attribute)
        self.session.commit()

        self.success({
            "message": "NetworkAttribute {} deleted from Site {}.".format(
                attribute_id, site_id
            ),
        })


class NetworksHandler(ApiHandler):
    def post(self, site_id):
        """ Create a new Network."""

    def get(self, site_id):
        """ Return all Networks. """


class NetworkHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return a specific Network. """

    def put(self, site_id, network_id):
        """ Update a Network. """

    def delete(self, site_id, network_id):
        """ Delete a Network. """


class NetworkIpsHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return allocated IPs for a Network."""


class IpsHandler(ApiHandler):
    def post(self, site_id):
        """ Create a new ip address."""

    def get(self, site_id):
        """ Return all ip addresses. """


class IpHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return a specific ip address """

    def put(self, site_id, network_id):
        """ Update a ip address """

    def delete(self, site_id, network_id):
        """ Delete a ip address """


class IpNetworksHandler(ApiHandler):
    def get(self, site_id, network_id):
        """ Return Networks this that contain this ip address. """


class ChangesHandler(ApiHandler):
    def get(self, site_id=None):
        """ Return Change events."""

        changes = self.session.query(models.Change)
        if site_id is not None:
            site = self.session.query(models.Site).filter_by(id=site_id).scalar()
            if not site:
                return self.notfound("No such Site found at id {}".format(site_id))
            changes = changes.filter_by(site_id=site_id)

        self.success({
            "changes": [change.to_dict() for change in changes],
        })


class NotFoundHandler(ApiHandler):
    def get(self):
        return self.notfound("Endpoint not found")
