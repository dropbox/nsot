import re

from tornado.web import RequestHandler, urlparse
from tornado.escape import utf8

from sqlalchemy.exc import IntegrityError

from .. import models
from .. import util


ATTRIBUTE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class ApiHandler(RequestHandler):
    def initialize(self):
        self.session = self.application.my_settings.get("db_session")()

    def on_finish(self):
        self.session.close()

    def error(self, errors):
        errors = [
            {"code": code, "message": message} for code, message in errors
        ]

        self.write({
            "status": "error",
            "errors": errors,
        })

    def success(self, data):
        self.write({
            "status": "ok",
            "data": data,
        })

    def error_status(self, status, message):
        self.set_status(status)
        self.error([(status, message)])
        self.finish()

    def badrequest(self, message):
        self.error_status(400, message)

    def notfound(self, message):
        self.error_status(404, message)

    def conflict(self, message):
        self.error_status(409, message)

    def created(self, location):
        self.set_status(201)
        self.set_header(
            "Location",
            urlparse.urljoin(utf8(self.request.uri), utf8(location))
        )
        self.finish()


class SitesHandler(ApiHandler):

    def post(self):
        """ Create a new Site."""
        name = self.get_argument("name")
        description = self.get_argument("description", "")

        try:
            site = models.Site(name=name, description=description).add(self.session)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))

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

        name = self.get_argument("name", None)
        description = self.get_argument("description", None)

        try:
            if name is not None:
                site.name = name
            if description is not None:
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


class AttributesHandler(ApiHandler):

    def post(self, site_id):
        """ Create a new Attribute."""

        name = self.get_argument("name")
        required = self.get_argument("required", None)
        cascade = self.get_argument("cascade", None)


        if not ATTRIBUTE_NAME.match(name):
            return self.badrequest("Invalid name parameter.")

        try:
            attribute = models.Attribute(site_id=site_id, name=name).add(self.session)
            if required is not None:
                attribute.required = util.qp_to_bool(required)
            if cascade is not None:
                attribute.cascade = util.qp_to_bool(cascade)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.created("/api/sites/{}/attributes/{}".format(site_id, attribute.id))

    def get(self, site_id):
        """ Return all Attributes."""
        attributes = self.session.query(models.Attribute).all()
        self.success({
            "attributes": [attribute.to_dict() for attribute in attributes],
        })


class AttributeHandler(ApiHandler):
    def get(self, site_id, attribute_id):
        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()
        if not attribute:
            return self.notfound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(site_id, attribute_id)
            )

        self.success({
            "attribute": attribute.to_dict(),
        })

    def put(self, site_id, attribute_id):
        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()
        if not attribute:
            return self.notfound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(site_id, attribute_id)
            )

        name = self.get_argument("name", None)
        required = self.get_argument("required", None)
        cascade = self.get_argument("cascade", None)

        try:
            if name is not None:
                if not ATTRIBUTE_NAME.match(name):
                    return self.badrequest("Invalid name parameter.")
                attribute.name = name

            # TODO(gary): Verify that all networks contain this attribute
            #             or fail when changed to True
            if required is not None:
                attribute.required = util.qp_to_bool(required)
            # TODO(gary): When changed to true add transitive attributes. When
            #             changed to false, remove transitive attributes.
            if cascade is not None:
                attribute.cascade = util.qp_to_bool(cascade)
            self.session.commit()
        except IntegrityError as err:
            return self.conflict(str(err.orig))

        self.success({
            "attribute": attribute.to_dict(),
        })

    def delete(self, site_id, attribute_id):
        attribute = self.session.query(models.Attribute).filter_by(
            id=attribute_id,
            site_id=site_id
        ).scalar()
        if not attribute:
            return self.notfound(
                "No such Attribute found at (site_id, id) = ({}, {})".format(site_id, attribute_id)
            )

        # TODO(gary): Remove all references to this attribute
        self.session.delete(attribute)
        self.session.commit()

        self.success({
            "message": "Attribute {} deleted from Site {}.".format(attribute_id, site_id),
        })


class SubnetsHandler(ApiHandler):
    def get(self, site_id):
        pass


class SubnetHandler(ApiHandler):
    def get(self, site_id, network_id):
        pass


class SubnetIpsHandler(ApiHandler):
    def get(self, site_id, network_id):
        pass


class IpsHandler(ApiHandler):
    def get(self, site_id):
        pass


class IpHandler(ApiHandler):
    def get(self, site_id, network_id):
        pass


class IpSubnetsHandler(ApiHandler):
    def get(self, site_id, network_id):
        pass


class IpHostnamesHandler(ApiHandler):
    def get(self, site_id, network_id):
        pass


class NotFoundHandler(ApiHandler):
    def get(self):
        return self.notfound("Endpoint not found")
