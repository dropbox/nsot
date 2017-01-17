#########
Changelog
#########

Version History
===============

.. _v1.1:

1.1 (2017-01-23)
----------------

* A formal :ref:`deprecation-policy` has been implemented which dictates a
  three-feature release cycle for removing deprecated API endpoints. Please see
  the documentation on this topic for more details.
* Fix #203 - Implementation of Circuits as a resource object.

  + A Circuit has one-to-one relationship with each of A and Z side
    endpoint Interfaces.
  + Circuits are resource objects and therefore may have attributes and
    support set query lookups.
  + A circuit must have at least an A-side endpoint defined. For circuits for
    which you do not own the remote end, you may leave the Z-side empty and
    specify the remote endpoint by customizing the circuit name.

* Circuits have the following detail routes available in the API:

  + ``circuits/:id/devices/`` - List peer devices on either end of circuit
  + ``circuits/:id/interfaces/`` - List interfaces bound to the circuit
  + ``circuits/:id/addresses/`` - List addresses bound to circuit interfaces

* Interfaces have a new ``interfaces/:id/circuit/`` detail route that will
  display the circuit to which an interface is bound.
* Devices have a new ``devices/:id/circuits/`` detail route that will
  display all circuits bound to interfaces on the device.
* Fix #191 - The Interface object unicode representation changed to
  ``device_hostname:name`` so that it can more easily be used as a slug for
  computing Circuit slug.
* Fix #230 - The misspelled ``networks/:id/descendents/`` API endpoint is
  pending deprecation in exchange for ``networks/:id/descendants/``.

.. _v1.0.13:

1.0.13 (2017-01-12)
-------------------

* Provides the ability to more efficiently access the device hostname
  associated with an interface, using the cached ``device_hostname`` field.
* Provides the ability access interface objects by natural key of
  ``device_hostname:name``.
  Ex. ``foo-bar1:eth1``

.. _v1.0.12:

1.0.12 (2017-01-12)
-------------------

* Fix #252 - Fixes bug in ``get_next_network`` for assigned networks of
	different prefix lengths

.. _v1.0.11:

1.0.11 (2017-01-10)
-------------------

* Fix #250 - Improves treatment of ``get_next_network`` and assigned state
* Fix #238 - Update to Docker instructions
* Fix #219 - Better handling of attempts to create objects in non-existent sites
* Moved Vagrantfile to root of repo

.. _v1.0.10:

1.0.10 (2016-12-05)
-------------------

* Fix for handling IPAddress defaults in migrations, to avoid attempting
  validation of a NULL default.

.. _v1.0.9:

1.0.9 (2016-11-23)
------------------

* Added missing database migrations related to having changed or added the
  ``verbose_name`` on a bunch of model fields prior to 1.0 release. No schema
  changes are actually made in the migration. This is being released so that
  some pending pull requests can be merged in more cleanly.

.. _v1.0.8:

1.0.8 (2016-10-24)
------------------

* Provides the ability to require uniqueness for results of queries using
  the optional ``unique=true`` param. Queries with multiple results
  that have this flag set will return an error. Implements #221.

.. _v1.0.7:

1.0.7 (2016-10-24)
------------------

* Implemented changes needed to upgrade to Django REST Framework v3.5.0
* Added `fields = '__all__'` to all default model serializers used for
  displaying objects
* Changes required for django-filter>=0.15 were made for filtersets
  using custom fields.

.. _v1.0.6:

1.0.6 (2016-10-18)
------------------

* Improve performance in Network.get_next_network() for large prefixes

  + The fix in #224 introduced a notable performance bug due to iterating
    all descendents vs. only direct children.
  + This patch addresses the performance issue by attempting to pre-seed
    the list of dirty networks via excluding ones with ineligible prefix
    lengths as well as immediately checking whether a candidate subnet is
    dirty BEFORE iterating child networks vs. AFTER.

.. _v1.0.5:

1.0.5 (2016-10-13)
------------------

* Fix #224 - Fixed a bug in ``Network.next_network()`` where a nested child
  (descendent) would continually be offered as free, even if it existed in the
  database. All descendent networks for a parent are now inspected when
  determining availability.

.. _v1.0.4:

1.0.4 (2016-09-29)
------------------

* Replaced ``settings.NETWORK_INTERCONNECT_PREFIXLEN`` (an integer) with
  ``settings.NETWORK_INTERCONNECT_PREFIXES`` (a tuple) to support IPv6
  prefixes, which defaults to prefixes (/31, /127).
* ``Network.next_address()`` was changed to calculate available addresses
  differently if the network from which you are allocating is determined to be
  an interconnect network. For interconnects, gateway and broadcast addresses
  can be returned. For any other networks, they cannot.

.. _v1.0.3:

1.0.3 (2016-09-08)
------------------

* Fix #216 - Fixed a bug in ``Network.next_network()`` where networks
  containing children were being offered as free. Networks are now only offered
  if they do not have any child networks.
* Fix #212 - Updated requirements to require ``djangorestframework>=3.4.4`` and
  removed ``nsot.api.serializers.LimitedForeignKeyField`` since this
  functionality is now built into DRF.

.. _v1.0.2:

1.0.2 (2016-08-31)
------------------

* Ubuntu 16.04 is now officially supported.
* Fix #213 - Updated requirements to utilize ``cryptography==1.5`` so that
  install will work on Ubuntu versions 12.04 through 16.04. (Credit:
  @slinderud)
* Finally fixed ``bump.sh`` to work on both Linux and Darwin. For real this
  time.

.. _v1.0.1:

1.0.1 (2016-07-08)
------------------

* Fix #209 - Fixed a bug in ``Network.closest_parent()`` that would sometimes
  cause an incorrect parent network to be returned when performing a "closest
  parent" lookup for a CIDR.

.. _v1.0:

1.0 (2016-04-27)
----------------

* OFFICIAL VERSION 1.0!!
* Completely documented all object fields including help_text, verbose_names,
  labels, default values, etc. for every field so that is cascades to
  serializers and form fields.

.. _v0.17.4:

0.17.4 (2016-04-22)
-------------------

* Fixed a bug in ``Network.next_address()`` and ``Network.next_network()``
  where children w/ busy states were mistakenly being excluded from the
  filter and therefore causing them to be offered as free. This also
  addressed a related bug where networks were not offered unless they
  came after the last prefix of the last matching child.

.. _v0.17.3:

0.17.3 (2016-04-21)
-------------------

+ Added documentation for set queries for both how they work and for how to use
  them.
+ Fixed a typo in Docker readme
+ Added an entry-point for ``snot-server`` because reasons

.. _v0.17.2:

0.17.2 (2016-04-17)
-------------------

* Filtering of Interfaces by ``mac_address`` can now be done using either the
  string (e.g. ``'00:00:00:00:00:01'``) or integer (e.g. ``1``)
  representations.

.. _v0.17.1:

0.17.1 (2016-04-07)
-------------------

* Fixed a bug that would cause set queries lookups of attributes values
  containing spaces to always fail. When performing a set queries for an
  ``attribute=value`` pair, if a value contains a space, it must be quoted, and
  it will be properly parsed.
* When performing a set query for an attribute that does not exist, an error is
  raised.
* When performing a set query, if no attribute pairs are found, an empty set is
  returned.
* Docs: Fixed a typo in data model doc
* Docs: Fixed incorrect year for a bunch of entries in changelog

.. _v0.17:

0.17 (2016-03-31)
-----------------

* **BACKWARDS INCOMPATIBLE** - API version 1.0 is now the global default.
* Fix #167 - Web UI has been updated to use API v1.0
* Ripped out all pre-v1 code.
* Updated the browsable API renderer to not display "filter forms", so
  that browsable API views with tons of results and related fields don't
  deadlock.

.. _v0.16:

0.16 (2016-03-29)
-----------------

* Finally added a login screen to the web UI.
* Fixes #130 - Redirect to login screen if a 401 is detected
* This adds HTTP interceptor for 401 responses that will redirect to the
  DRF API login web screen.
* Also skinned the default DRF login screen to match the NSoT theme.
* Stopgap fix in ``services.js`` to check for ``response.status``. This will
  have to be adjusted as a part of the API version 1.0 migration, along
  with all of the other JS code.

.. _v0.15.10:

0.15.10 (2016-03-28)
--------------------

* Fix #168 - Fix a 500 when assigning address that is in multiple sites

.. _v0.15.9:

0.15.9 (2016-03-17)
-------------------

* Bring a lot of documentation up to speed for readthedocs.org
* Added docstrings in places where there were none.
* Added code examples to some docstrings
* Updated requirements: Django==1.8.11

.. _v0.15.8:

0.15.8 (2016-03-12)
-------------------

* Fixes #171: Implemented API support for lookup by closest parent
* This implements a new detail route on the Networks endpoint at
  ``networks/{cidr}/closest_parent/``. The Network need not exist in the
  database and if found, the closest matching parent network will be
  returned.
* The endpoint also accepts a ``prefix_length`` argument to optionally
  restrict how far it will recurse to find possible parents.

.. _v0.15.7:

0.15.7 (2016-03-12)
-------------------

* Migrated to built-in filtering of Interface objects in API.
* Also added the ability to filter by ``device__hostname``, e.g.
  ``GET /api/interfaces/?device__hostname=foo-bar1``

.. _v0.15.6:

0.15.6 (2016-03-10)
-------------------

* Fixes #169: Bugfix when filtering objects by 'attributes' in list view
* Fixed a bug that would result in a 500 crash when filtering by
  attributes in list view if multiple sites have matching objects.
* Fixes #166: Added a settings toggle to display IPv6 in compressed
  form. (See: ``settings.NSOT_COMPRESS_IPV6``)

.. _v0.15.5:

0.15.5 (2016-03-08)
-------------------

* Bugfix to filtering networks in API and bump.sh and update requirements.
* Fixed shebang in ``bump.sh`` and used it to bump the version!
* Upgrade requirements: certifi==2016.2.28
* Bugfix in API filtering for Network objects that would result in an
  empty set if both ``include_ips`` and ``include_networks`` were set to
  ``True``.
* Added unit tests to extercise ``include_ips/include_networks`` filters,
  because come on.

.. _v0.15.4:

0.15.4 (2016-03-02)
-------------------

* Made authentication API endpoints version-aware.

  + Overlooked the API authentication endpoints when doing the
    API versioning.

* Moved API version header to root of tests so that the "API version"
  message shows up on all executions of unit tests.
* Updated requirements django-rest-swagger==0.3.5.

.. _v0.15.3:

0.15.3 (2016-02-29)
-------------------

* Complete overhaul of API filtering to use DRF built-in filtering.
* All overloads in views of .get_queryset() has been removed and
  replaced with ``filter_class`` objects stored in ``nsot.api.filters``
* All Resource filtering is now done using built-in
  ``DjangoFilterBackend`` objects using either ``filter_class`` or
  ``filter_fields``.

.. _v0.15.2:

0.15.2 (2016-02-24)
-------------------

* Fixes #118 - Network objects are now round-trippable in API.

  + You may now provide either ``cidr`` or ``network_address`` +
    ``prefix_length`` when creating a Network object.
  + A Network object returned by the API may now be full used for create
    or update, making them round-trippable.

* Verbose names and help text have been added to all Network fields, so
  that they display all pretty like.

.. _v0.15.1:

0.15.1 (2016-02-23)
-------------------

* Added X-Forward-For into request logging.
* Also added an API test for sending X-Forward-For

.. _v0.15:

0.15 (2016-02-22)
-----------------

* Full support for PATCH in the API and some resultant bug fixes to PUT.

  + Specifically, this means any resource that is allowed to have
    attributes can now be partially updated using PATCH, because PATCH
    operations have been made attribute-aware.
  + Attributes themselves cannot YET be partially updated, but we hope to
    address that in a future... PATCH.

* Serializers

  + PATCH support enabled for complex objects: Attributes, Devices,
    Interfaces, Networks.
  + ResourceSerializer subclasses now all inherit default behavior for
    handling attributes. The ``.create()`` and ``.update()`` methods now take
    an optional ``commit=`` argument to toggle whether to save an object after
    updating attributes. This is so that descendent serializers subclasses
    can overload this method and not call save until they choose (such as
    in Interface serializers).
  + Each resource now has PUT and PATCH serializers broken out explicitly
    to facilitate the "optional fields" nature of PATCH vs. the "mandatory
    fields" nature of PUT.

* Attributes

  + All error messages raised when validating attributes include the word
    "attributes" so that you know it's a validation error specific to
    attributes.

* Bug Fixes

  + Bugfix in handling PUT requests where attributes would be initialized
    if not provided. Attributes are now mandatory on any PUT requests and
    will result in an error if they are missing.
  + Bugfix when assigning more than one IP address from the same network
    to an
    Interface that would result in a 500 error (and unit tests now catch
    this).

.. _v0.14.2:

0.14.2 (2016-02-19)
-------------------

* Bugfixes w/ natural_key lookups that would result in a 500 error.

  + Turns out that ``site_pk`` was incorrectly being dropped when doing
    natural_key lookups, which would result in a 500 w/ multiple
    sites.
  + We now detect when multiple objects are returned when looking up
    resources by natural_key and display a helpful 400 error.
  + Reverted top-level URL router back to Bulk default router because the
    SimpleRouter base doesn't provide api-root, and we kind of (really)
    want that.

.. _v0.14.1:

0.14.1 (2016-02-19)
-------------------

* Issue #50 - Adds better device name validation
* Fixed regex to match DNS hostname requirements. Added unit tests for device name checking
* Fix device name / attribute name comment

.. _v0.14:

0.14 (2016-02-17)
-----------------

* Implement GET/PUT objects by natural_key and minor fixes.

* General

  + Upgraded ``drf-nested-routers==0.11.1``
  + Re-organized nsot.api.urls to improve readability
  + Implemented natural_key mappings for Device and Network resources

* Networks

  + Updated ``Network.objects.get_by_address()`` to support optional site=
    argument for filtering by site_id.

* Serializers

  + Moved ``.create()``, ``.update()`` methods from Device, Network serializers
    to new ``ResourceSerializer`` base.

* Change Events

  + Fix when deleting a resource object using the API failed for any
    reason the "Delete" change event would still be created. The Change
    event will now only be kept *after* a successful delete.

* Views

  + Implemented ``NsotViewSet.get_object()`` support for nested serializers
  + Updated Network lookup_value_regex to support loookup by pk or
    IPv4/IPv6 natural_key.

.. _v0.13.2:

0.13.2 (2016-02-16)
-------------------

* Fix #142 - Properly catch non-serializer errors in API views.
* This includes unique constraints and integrity errors.
* Added a regression test for this error case.

.. _v0.13.1:

0.13.1 (2016-02-11)
-------------------

* Fixes #82: Implemented for regex-based attribute lookups via the API.
* You now may append ``_regex`` to an attribute name in a set query and
  provide a regex pattern as the value to perform regex-based lookups.

.. _v0.13:

0.13 (2016-02-02)
-----------------

* Implement API filtering for value objects & perf. tweaks (Fixes #137)
* Value objects now have a site_id attribute that is hidden and
  automatically populated by their parent Attribtue, similarly to
  Interface objects and their parent Device.
* New API endpoint: ``/api/sites/:site_id/values/``
* Improved performance when creating/updating Interface objects by not
  explicitly looking up the parent Device object EVERY time.

.. _v0.12.7:

0.12.7 (2015-12-23)
-------------------

* Small tweaks to web UI
* Site index page

  + Interface count now added to Site dashboard
  + Links for ipv4/6 and network usage now link to filtered Network list
  + "Changes" renamed to "Recent Changes"
  + Under "Network Usage", "In Use" renamed to "Assigned"

* Networks list

  + Added "ip_version" filter
  + Columns now link to filtered Network list

.. _v0.12.5:

0.12.5 (2015-12-18)
-------------------

* Upgrade to Django==1.8.7 and DRF==3.3.2
* Filter fields now implemented in Browsable API (new in DRF 3.3)
* Added django-crispy-forms as a dependency
* Bootstrap JS updated to v3.3.5
* Bower updated to include Bootstrap fonts (DRF 3.3. needs this)

.. _v0.12.4:

0.12.4 (2015-12-09)
-------------------

* Made ``include_ips=True`` default when retrieving Networks (fix #120)

.. _v0.12.3:

0.12.3 (2015-12-04)
-------------------

* Implemented basic support for Interfaces in Web UI.

  + Create, update, delete all work
  + Device still only showing by id, should be displayed by hostname
  + Type only showing by id, should be displayed as selection of
    human-readable names derived from the schema.

.. _v0.12.2:

0.12.2 (2015-12-03)
-------------------

* Use native 'inet' type for storing IPs in PostgreSQL. (fixes #128)

.. _v0.12.1:

0.12.1 (2015-11-19)
-------------------

* Fix 500 crash when querying OPTIONS to view schema in API (fixes #126)

  + The bulk update mixin had to be subclassed to utilize super(), because
    it does not extend a pre-existing django-rest-framework mixin.
  + The inheritance order of the bulk mixins used in the Resource viewset
    also had to be changed because of this.

* Cleanup: The viewset for Attributes now inherits from ResourceViewSet.
* Cleanup: The viewset for Sites has been moved before ResourceViewSet
  for better readability (because Site is not a Resource type).

.. _v0.12:

0.12 (2015-11-17)
-----------------

* Basic concept of Network states, one of which is 'reserved'.
* Interaction w/ Interfaces to set state='assigned' on Assignment.
* Basic API endpoint to view ``/api/networks/reserved/`` to view reserved
  Networks.

.. _v0.11.7:

0.11.7 (2015-10-29)
-------------------

* Implemented more backend gunicorn options for default http service

  + max-requests: Max requests per worker before restart
  + max-requests-jitter - Random jitter in seconds between worker restart
  + preload - Whether to preload app before forking

.. _v0.11.6:

0.11.6 (2015-10-22)
-------------------

* Disabled caching by default (set to dummy caching)
* Added a section in the config docs for caching.
* Updated ``requirements-dev.txt`` to (re-)include ``sphinx-autobuild``

.. _v0.11.5:

0.11.5 (2015-10-20)
-------------------

* Update Interface serializer to properly encode None as JSON.

  + It was encoding it as a string (``'None'``) vs. objects (``null``)

.. _v0.11.4:

0.11.4 (2015-10-20)
-------------------

* Fix to allow null values for MAC address on Interfaces.
* Serializer and model fields now allow MAC to be set to None.
* Also added missing lines to MANIFEST.in causing missing
  static/templates, which is problematic for new dev. environments or
  external contributors.

.. _v0.11.3:

0.11.3 (2015-10-20)
-------------------

* MAC address bugfix and a little cleanup in exceptions and validation
* Integers are no longer being improperly cast to strings and then back
  to an incorrect integer representation. (fixes #111)
* Added extra unit tests and regression tests for this bug.
* Moved all references to exceptions into ``nsot.exc``.
* Moved email validator to ``nsot.validators``.

.. _v0.11.2:

0.11.2 (2015-10-16)
-------------------

* Updated nsot-server management commands to Django 1.8 syntax
* Bugfix in user_proxy in string formatting on startup
* Implemented support for ``-v/--verbosity`` flag in nsot-server commands to
  adjust loglevel (fix #59)
* Cleaned up the gunicorn service to read from CLI args
* Updated ``test_settings.py`` to include some of the newer settings.

.. _v0.11.1:

0.11.1 (2015-10-15)
-------------------

* Made gunicorn worker timeout configurable by CLI or settings.py
* New setting: ``settings.NSOT_NUM_WORKERS`` (default: 4) to tweak number
  of workers
* New setting: ``settings.NSOT_WORKER_TIMEOUT`` (default: 30) to tweak
  default worker timeout
* ``nsot-server start`` now takes a ``-t/--timeout`` option at runtime to
  override globald defaults.

.. _v0.11:

0.11 (2015-10-15)
-----------------

* Enabled caching for Interface API endpoints.
* Cache is invalidated on save or delete of an Interface object.

.. _v0.10.6:

0.10.6 (2015-10-13)
-------------------

* Removed stale deps. and updated core deps. to latest stable versions

.. _v0.10.5:

0.10.5 (2015-10-13)
-------------------

* Bugfix when explicitly setting ``parent_id=None`` on Interface create.

.. _v0.10.4:

0.10.4 (2015-10-13)
-------------------

* Implemented bulk update of all objects using the REST API.
* Objects can now be bulk-updated using PUT by providing a list of
  updated objects as the payload.
* Unit tests have been updated accordingly to test for both bulk create
  and bulk update.

.. _v0.10.3:

0.10.3 (2015-10-08)
-------------------

* Added a Vagrantfile, improved documentation, and made some UX fixes.
* Read auth header from settings vs. hard-coded inside of user_proxy
  command (fix #57)
* User proxy now also defers to default values from within settings.py
* Added a vagrant directory containing a Vagrantfile to bootstrap NSoT
  in a self-contained virtual machine
* Added a new 'assignments' endpoint for Networks, to tell where they
  are being
  assigned to Interfaces.
* Added new nsot.utils.stats and ability to calculate network
  utilization.

.. _v0.10.2:

0.10.2 (2015-10-08)
-------------------

* Always return empty query when set query is invalid (fix #99)

.. _v0.10.1:

0.10.1 (2015-10-08)
-------------------

* Improved indexing on common attribute-value lookups.
* All attribute-value lookups are index now by the most commonly used
  search patterns (name, value, resource_name) and (resource_name,
  resource_id)
* Moved Interface.get_networks() and Interface.get_addresses() to used
  concrete JSON cache fields on the objects. This is a huge query-time
  optimization.
* Tweaked admin panel fields a little bit to remove references to now
  defunct 'Resource' objects.

.. _v0.10:

0.10 (2015-10-05)
-----------------

* Overhauled the relationship between Values and Resources.
* Drastic performance improvement and more accurate indexing of
  attribute Values in databases with millions of rows.
* Got rid of multi-table inheritance from base Resource model that was
  used to allow a generic foreign key from attribute Values to Resources
  (Devices, Networks, Interfaces are all resources)
* All Resource subclasses are *abstract* now. Which means the model
  fields they inherit are concrete on their own table.
* The Value object does not have an FK, and instead has a composite
  primary key to (resource_name, resource_id) … for example ('Device',
  16999) which is indexed together.
* The Attribute name is now also stored in a concrete field on the
  Value at creation, eliminating a lookup to the Attribute table.
* All of these changes are accounted for in the database migrations, but
  need to be done carefully! It's going to be quicker and easier for
  databases that don't have Interfaces.

.. _v0.9.4:

0.9.4 (2015-10-02)
------------------

* Bug and performance fixes for Interface objects.
* Fix poor performance when there are lots of Interface objects.
* Bugfix to missing interface type 53 (proprietary virtual/internal)
* Added ``smart_selects==1.1.1`` so that FK lookups on Interface.parent
  will be limited to owning Device.
* Temporarily convert Interface.parent_id to raw ID field, until an
  autocomplete feature can be added to the browsable API.
* Updated unit tests to validated CRUD for Interface.parent_id.

.. _v0.9.3:

0.9.3 (2015-09-30)
------------------

* Fix a 500 crash when database ``IntegrityError`` happens.

  + This will now be treated as a ``409 CONFLICT``.

.. _v0.9.2:

0.9.2 (2015-09-30)
------------------

Schema change to fix confusion when selecting parent objects.

* Benchmarks for Network and Interface objects are a *little* faster now
  too, direct table access for parent.
* Device objects no longer have an extraneous parent attribute.

.. _v0.9.1:

0.9.1 (2015-09-29)
------------------

* Enhanced and clarified sections in README.rst
* Converted README from .md to .rst
* Clarified virtualenvwrapper instructions (fix #90)
* Made use of git clone more explicit (fix #91)
* Updated required version of Django REST Framework to v3.2.4

.. _v0.9:

0.9 (2015-08-06)
----------------

* Implemented top-level Interface resource object.
* Addresses are assigned to Interfaces by way of Assignment objects,
  which are used to enforce relationship-level constraints on the
  assignment of Network objects to Device Interfaces.
* A Device can zero or more Interfaces; an Interface can have multiple
  addresses, and addresses are 'assigned' to Interfaces
* Networks are derived as the parent networks of the addresses for each
  interface.
* Moved hard-coded variable data in models.py into module-global
  constants.
* Renamed all model "choices" lists to end in "_CHOICES"
* New requirements: django-macaddress v1.3.2, Django v1.8.4
* Updated README.md to include IRC mention.
* All constants moved from ``nsot.constants`` to ``nsot.conf.settings`` and
  ``nsot.constants`` has been eliminiated. (fix #87)
* All data validators have been moved to ``nsot.validators`` and added new
  validators for cidr and host addresses.
* Moved ``.to_representation()`` methods on all 'resource' serializers to
  the top-level ``nsot.api.serializers.NsotSerializer``
* Fixed a crash when creating ``Network`` objects without the CIDR being
  unicode.
* Fixed a bug when looking up a single object in API without providing
  site_pk
* Moved IP_VERSIONS and HOST_PREFIXES into settings.py
* IP assignments must now be unique to a device/interface tuple.
* Addresses can now be explicitly assigned to an interface, or
  overwritten
* Added a new ``nsot.serializers.JSONListField`` type to serialize JSON
  <-> Python lists
* Added util for deriving attributes from custom model fields that
  required custom serializer fields.
* Added ``tests.api_tests.util.filter_interfaces`` for simplifying
  ``Interface`` testing.
* Added 'ip_version' as a filter field for ``Network`` API lookups.

.. _v0.8.6:

0.8.6 (2015-07-29)
------------------

* Add remote IP address in request logger.

.. _v0.8.5:

0.8.5 (2015-07-24)
------------------

* Broke out media (css, etc.), nav, and scripts into their own include
  files.
* Updated main FeView to inherit default template context
* Added a template context processor to globally modify template
  context to inject app version.
* Added API and API Reference to dropdown "gear" menu
* Fix #77 - Only collect static files on ``nsot-server start`` if
  ``settings.SERVE_STATIC_FILES=True``.

.. _v0.8.4:

0.8.4 (2015-07-20)
------------------

* Fix including of static files in setup.py install.
* Also make sure that tests packages aren't included.

.. _v0.8.3:

0.8.3 (2015-07-20)
------------------

* Improvements to managing static files and other server mgmt fixups.
* The default ``STATIC_ROOT`` setting has been changed back to
  ``$BASE_DIR/staticfiles``
* Added 'staticfiles' to ``.gitignore``
* The 'nsot-server start' command has been updated to collect the static
  files automatically. This can be disabled by passing
  ``--no-collectstatic``.
* Renamed ``nsot-server --noupgrade`` to ``--no-upgrade``
* Added help text to ``nsot-server start`` arguments.
* Added a URL redirect handler for ``favicon.ico`` (fixes #73) and
  included a placeholder favicon and included a ``<link>`` in the web UI
  template.
* Replaced package_data in ``setup.py`` with grafting files in
  ``MANIFEST.in``
* Updated the ``setup.py sdist`` command to *truly* include the built
  static files prior to making the distribution.
* Updated Django requirement to v1.8.3

.. _v0.8.2:

0.8.2 (2015-07-19)
------------------

* Large update to FE build/dist!
* We're now using npm to manage our frontend dev dependencies and gulp to
  manage our front end builds
* Add some node files and built assets to .gitignore
* Gulp added w/ tasks for linting, caching templates, annotating ng DI,
  concat, minify, etc.
* Setup npm devDependencies and shrinkwrap them for consistent build
* Relocated js/css into src directory that isn't included with dist build
* Updated angular code to not explicitly put DI params twice since that
  happens at build
* Angular templates are now compiled to javascript and added to the
  template cache
* Fixed some lint errors (semicolons!)
* setup.py updated to support running all tests (python & javascript)
* setup.py updated to build static on develop/sdist commands
* Removed 3rd party deps from the checked in repo
* Fixed MANIFEST.in to not include pyc's under tests

.. _v0.8.1:

0.8.1 (2015-07-16)
------------------

* Implement network/address allocation endpoints for Network objects.
* For database models the following methods have been added:

  + ``get_next_address()`` - Returns a list of next available a addresses
    (fixes #49)
  + ``get_next_network()`` - Returns a list of next available networks
    matching the provided prefix_length. (fixes #48)

* For the REST API, the following endpoints have been added to Network
  objects in detail view (e.g. ``GET /api/sites/1/networks/10/:endpoint1``):

  + ``next_address`` - Returns a list of next available a addresses
  + ``next_network`` - Returns a list of next available networks
    matching the provided prefix_length.
  + ``parent`` - Return the parent Network for this Network

+ Updated all of the tree traversal methods to explicitly order results
  by (network_address, prefix_length) so that results are in tree order.
+ Corrected a typo in the README file (fixes #69)
+ All new functionality is completely unit-tested!

.. _v0.8:

0.8 (2015-07-16)
----------------

* Implement tree traversal endpoints for Network objects.
* For database models the following methods have been added:

  + ``is_child_node()`` - Returns whether Network is a child node
  + ``is_leaf_node()`` - Returns whether Network has no children
  + ``is_root_node()`` - Returns whether Network has no parent
  + ``get_ancestors()`` - Return all parents for a Network
  + ``get_children()`` - Return immediate children for a Network
  + ``get_descendents()`` - Return ALL children for a Network
  + ``get_root()`` - Return the root node of this Network
  + ``get_siblings()`` - Returns Networks with the same parent

* For the REST API, the following endpoints have been added to Network
  objects detail view (e.g. ``GET /api/sites/1/networks/10/:endpoint``):

  + ``ancestors`` - Return all parents for a Network
  + ``children`` - Return immediate children for a Network
  + ``descendents`` - Return ALL children for a Network
  + ``root`` - Return the root node of this Network
  + ``siblings`` - Returns Networks with the same parent

* All new functionality is completely unit-tested!

.. _v0.7.4:

0.7.4 (2015-07-14)
------------------

* Multiple bug fixes related to looking up Attributes using set queries.
* Fix #66 - Handle 500 error when multiple Sites contain an Attribute of the
  same name.
* Fix #67 - Bugfix when an Attribute name isn't found when performing a set
  query.
* Resource.objects.set_query() now takes an optional site_id argument
  that will always be sent when called internally by the API.
* Added site_id to repr for Attribute objects to make it less confusing
  when working with multiple sites containing Attributes of the same
  name.
* Fixed a bug in Attribute.all_by_name() that would cause the last
  Attribute matching the desired name, even if the site_id conflicted
  with the parent resource object. Attribute.all_by_name() now requires
  a site argument.
* If a set query raises an exception (such as when no matching Attribute
  is found), an empty queryset is returned.

.. _v0.7.3:

0.7.3 (2015-07-09)
------------------

* Fix #58: Typo in permissions docs
* Fix #64: New command to generate key

.. _v0.7.2:

0.7.2 (2015-07-07)
------------------

* Fix #62 - 500 error when API authenticate is malformed.

.. _v0.7.1:

0.7.1 (2015-07-02)
------------------

* Remove need to "collectstatic", remove 'nsot.log' log handler.

  + Static files will default to being served from within the nsot
    library itself, eliminating the need to colectstatic.
  + nsot-server will no longer drop an empty nsot.log file in the
    directory from which it is called.

.. _v0.7:

0.7 (2015-07-01)
----------------

* Replace backend with Django + Django REST Framework + Gunicorn + Gevent

.. _v0.5.6:

0.5.6 (2015-06-15)
------------------

* Actually pass num_processes down to tornado

.. _v0.5.5:

0.5.5 (2015-06-11)
------------------

* Fix #46: Purge attribute index before a Device object is deleted.

.. _v0.5.4:

0.5.4 (2015-06-08)
------------------

* Update libs and small UI fixes

  + Add filter options to networks page
  + css cleanup
  + Fix bug where all changes were for site id 1. fixes #51
  + Update libraries to later versions to get some new features.

.. _v0.5.3:

0.5.3 (2015-05-29)
------------------

* Bugfix in validating Attribute when constraints are not dict.

.. _v0.5.2:

0.5.2 (2015-04-13)
------------------

* Fix #40 Auth token verification now uses session from request handler

  + This is very difficult to reproduce, so changing the request handler
    (which is currently the only caller of User.verify_auth_token()) to
    send its own session when calling is a best guess at solving this.k

.. _v0.5.1:

0.5.1 (2015-04-13)
------------------

* Fix #41 so set queries on networks include optional filter arguments.

.. _v0.5:

0.5 (2015-04-07)
----------------

+ Add support for logging errors to Sentry if sentry_dsn is set.

.. _v0.4.4:

0.4.4 (2015-04-02)
------------------

* Bugfix for displaying IPs when filtering Networks w/ attrs. (fix #34)
* Added some extra networks to the test fixtures for API tests.
* Updated fixtures for network set queries to reflect extra networks.

.. _v0.4.3:

0.4.3 (2015-04-01)
------------------

* UI Updates

  + fixes #19
  + fixes #32

* Show attributes on Device/Network pages.
* Show latest changes on Device/Network pages.
* Provide NSOT_VERSION to jinja and angular templates.
* Show version in NSoT UI

.. _v0.4.1:

0.4.1 (2015-03-31)
------------------

+ Only import mrproxy for user_proxy arg in nsot-ctl. (fixes #24)

.. _v0.4:

0.4 (2015-03-31)
----------------

+ Add support for filtering networks by cidr/addr/prefix/attrs. (fix #18)

.. _v0.3.3:

0.3.3 (2015-03-30)
------------------

+ If restrict_networks is null, treat it as an empty list. (fix #22)

.. _v0.3.2:

0.3.2 (2015-03-30)
------------------

* Explicitly include and order all dependent packages.

  + This is so that enum34 (dependency of cryptography) can be properly
    installed using an internal PyPI mirror (See:
    https://github.com/pyca/cryptography/issues/1803)

* Removed six from requirements-dev.txt
* Bumped version to differentiate these underlying changes.

.. _v0.3.1:

0.3.1 (2015-03-19)
------------------

+ Allow lookup of Devices by hostname or attributes.

.. _v0.3:

0.3 (2015-03-12)
----------------

* Added support for set operation queries on Devices and Networks.
* New "query" endpoint on each of these resources take a "?query="
  argument that is a string representation of attribute/value pairs for
  intersection, difference, and union operations.
* All new functionality unit tested!

.. _v0.2.2:

0.2.2 (2015-03-06)
------------------

+ Bugfix for 500 error when creating Network w/ null cidr (fixes #13)

.. _v0.2.1:

0.2.1 (2015-03-05)
------------------

- Bug fix for 500 error when validating null hostname (fixes #11)

.. _v0.2.0:

0.2.0 (2015-03-04)
------------------

* Added support for bulk creation of Attributes, Devices, and Networks
* When creating a collection via POST, a 201 CREATED response is
  generated without a Location header. The payload includes the created
  objects.

.. _v0.1.0:

0.1.0 (2015-02-28)
------------------

* Bugfix in string format when validating attribute that doesn't exist.

.. _v0.0.9:

0.0.9 (2015-02-10)
------------------

* Implemented API key (auth_token) authentication
* Cookies are now stored as secure cookies using cookie_secret setting.
* New site setting for storing secret_key used for crypto.
* User has a new .secret_key field which is generated when User is
  created

  + User should obtain key through web UI (however that is NYI)
  + Secret key is used as user password to generate an auth_token

* Auth token is serialized, and encrypted with server's key and also
  contains an expiration timestamp (default 10 minutes)
* AuthToken can be done using "Authorization" header or query args.
* New User methods for generating and validating auth_token
* API endpoints still also accept "default" login methods.
* Added a models.get_db_session() function to make getting a session
  easier!
* Added a Model.query classmethod to make model queries easier!!
* All new changes are unit tested!
* If you're checking out the API auth stuff and want to test it out, see
  the README.auth.rst file!
* Web views use "default" auth (currently user_auth_header)
* API views use "default" or "auth_token"
* AuthToken can now be done using "Authorization" header or query args.

.. _v0.0.2:

0.0.2 (2015-01-12)
------------------

* Add setting to toggle for checking XSRF cookies on API calls.

.. _v0.0.1:

0.0.1 (2014-12-03)
------------------

* Initial scaffolding for NSoT
* Python packaging
* Inital models
* Support for add/remove/update/list Sites
