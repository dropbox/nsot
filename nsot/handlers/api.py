from tornado.web import RequestHandler, urlparse
from tornado.escape import utf8

from sqlalchemy.exc import IntegrityError

from .. import models


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

    def conflict(self, message):
        self.set_status(409)
        self.error([(409, message)])
        self.finish()

    def notfound(self, message):
        self.set_status(404)
        self.error([(404, message)])
        self.finish()

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
