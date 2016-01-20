(function() {
    "use strict";

    var app = angular.module("nsotApp");

    app.controller("navigationController", function($scope, $location) {

        $scope.siteId = null;
        $scope.$on('$routeChangeStart', function(next, current) {
            $scope.siteId = current.params.siteId;
        });

        $scope.isActive = function(str){
            var path = $location.path();
            return path === str;
        };

    });

    app.controller("IndexController", function($location, Site) {

        Site.query(function(response){
            var sites = response.data;
            if (!sites.length || sites.length > 1) {
                $location.path("/sites");
            } else {
                // If there's a single site, just go there.
                $location.path("/sites/" + sites[0].id);
            }
            $location.replace();
        });
    });

    app.controller("ProfileController", function(Users, $location, $q) {
        $q.all([
            Users.one(0).get(),
        ]).then(function(results){
            $location.path("/users/" + results[0].id);
        });

    });

    app.controller("SitesController", function($scope, $q, $location, Site, User) {

        $scope.loading = true;
        $scope.sites = [];
        $scope.user = null;
        $scope.site = new Site();
        $scope.error = null;

        $q.all([
            User.get({id: 0}).$promise,
            Site.query().$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.sites = results[1].data;

            $scope.loading = false;
        });

        $scope.createSite = function(){
            $scope.site.$save(function(site){
                $location.path("/sites/" + site.id);
            }, function(data){
                $scope.error = data.data.error;
            });
        };
    });

    app.controller("SiteController",
            function($scope, $route, $location, $q, $routeParams, Site, User,
                     Device, Network, Change, Interface) {

        $scope.loading = true;
        $scope.user = null;
        $scope.site = null;
        $scope.total_devices = null;
        $scope.total_interfaces = null;
        $scope.total_networks = null;
        $scope.total_ipv4 = null ;
        $scope.total_ipv6 = null;
        $scope.total_reserved = null;
        $scope.total_allocated = null;
        $scope.total_assigned = null;
        $scope.total_orphaned = null;
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        $scope.changes = [];

        var siteId = $routeParams.siteId;

        var netsets = {
            siteId: siteId,
            include_ips: true,
            limit: 1
        }
        var net4 = {
            siteId: siteId,
            include_ips: true,
            ip_version: 4,
            limit: 1
        } 
        var net6 = {
            siteId: siteId,
            include_ips: true,
            ip_version: 6,
            limit: 1
         }
        var ipam_reserved = {
            siteId: siteId,
            include_ips: true,
            state: "reserved",
            limit:1
        }
        var ipam_allocated = {
            siteId: siteId,
            include_ips: true,
            state: "allocated",
            limit: 1
        }
        var ipam_assigned = {
            siteId: siteId,
            include_ips: true,
            state: "assigned",
            limit: 1
        }
        var ipam_orphaned = {
            siteId: siteId,
            include_ips: true,
            state: "orphaned",
            limit: 1
        }
        var change_go = {
            siteId: siteId,
            limit: 10
        }

        $q.all([
            User.get({id: 0}).$promise,
            Site.get({id: siteId}).$promise,
            Device.query({siteId: siteId, limit:1}).$promise,
            Network.query(netsets).$promise,
            Network.query(net4).$promise,
            Network.query(net6).$promise,
            Network.query(ipam_reserved).$promise,
            Network.query(ipam_allocated).$promise,
            Network.query(ipam_assigned).$promise,
            Network.query(ipam_orphaned).$promise,
            Change.query(change_go).$promise,
            Interface.query({siteId: siteId, limit:1}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.site = results[1];
            $scope.total_devices = results[2].total;
            $scope.total_networks = results[3].total;
            $scope.total_ipv4 = results[4].total;
            $scope.total_ipv6 = results[5].total;
            $scope.total_reserved = results[6].total;
            $scope.total_allocated = results[7].total;
            $scope.total_assigned = results[8].total;
            $scope.total_orphaned = results[9].total;
            $scope.changes = results[10].data;
            $scope.total_interfaces = results[11].total;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);
            $scope.loading = false;

            // BEG chart
            $scope.labels = [
                "Assigned",
                "Allocated",
                "Reserved",
                "Orphaned"
            ];
            $scope.data = [
                $scope.total_assigned,
                $scope.total_allocated,
                $scope.total_reserved,
                $scope.total_orphaned
            ];
            // END chart
        });

        $scope.updateSite = function(){
            $scope.site.$update(function(){
                $route.reload();
            }, function(data){
                $scope.updateError = data.data.error;
            });
        };

        $scope.deleteSite = function(){
            $scope.site.$delete(function(){
                $location.path("/sites");
            }, function(data){
                $scope.deleteError = data.data.error;
            });
        };
    });

    app.controller("UsersController",
            function($scope, $route, $location, $q, $routeParams) {
        $scope.loading = true;
    });

    app.controller("UserController",
            function($scope, $route, $location, $q, $routeParams, Users) {

        $scope.loading = true;
        $scope.currentUser = null;
        $scope.profileUser = null;
        $scope.secret_key = null;
        var userId = $routeParams.userId;
        $scope.isSelf = false;

        $scope.showKey = function(){
            Users.one(userId).get({with_secret_key: true}).then(function(data) {
                $scope.secret_key = data.secret_key;
            });
        };

        $scope.rotateKey = function(){
            $scope.profileUser.rotateSecretKey().then(function(new_key){
                $scope.secret_key = new_key;
            });
        };

        $q.all([
            Users.one(0).get(),
            Users.one(userId).get()
        ]).then(function(results){
            $scope.loading = false;
            $scope.currentUser = results[0];
            $scope.profileUser = results[1];
            $scope.isSelf = $scope.currentUser.id === $scope.profileUser.id;
        });
    });

    app.controller("NetworksController",
            function($scope, $location, $q,  $routeParams,
                     User, Network, Attribute, pagerParams, Paginator) {
        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = {};
        $scope.networks = [];
        $scope.paginator = null;
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $scope.formMode = "create";
        $scope.formUrl = "includes/networks-form.html";
        $scope.formData = {
            attributes: []
        };
        $scope.ip_versions = ['4', '6'];
        $scope.states = ['allocated', 'assigned', 'reserved', 'orphaned'];

        $scope.filters = {
            include_ips: nsot.qpBool($routeParams, "include_ips", true),
            include_networks: nsot.qpBool($routeParams, "include_networks", true),
            root_only: nsot.qpBool($routeParams, "root_only", false),
            ip_version: $routeParams.ip_version,
            state: $routeParams.state
        };

        var params = _.extend(pagerParams(), {
            siteId: siteId,
        }, $scope.filters);

        $q.all([
            User.get({id: 0}).$promise,
            Network.query(params).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.networks = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);


            $scope.paginator = new Paginator(results[1]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#createNetworkModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Network"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});

                $scope.formData.attributes = _.chain($scope.attributes)
                    .filter(function(value){
                        return value.display;
                    })
                    .sortBy(function(value){
                        return value.required ? 0 : 1;
                    })
                    .map(function(value){
                        return {
                            name: value.name
                        };
                    }).value();
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#createNetworkModal");
        });


        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.createNetwork = function() {
            var network = Network.fromForm($scope.formData);
            network.$save({siteId: siteId}, function(network){
                $location.path("/sites/" + siteId + "/networks/" + network.id);
            }, function(data){
                $scope.error = data.data.error;
            });
        };

    });

    app.controller("NetworkController",
            function($scope, $route, $location, $q, $routeParams,
                     User, Network, Attribute, Change) {

        $scope.loading = true;
        $scope.user = {};
        $scope.network = {};
        $scope.attributes = {};
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        var siteId = $scope.siteId = $routeParams.siteId;
        var networkId = $scope.networkId = $routeParams.networkId;
        $scope.formMode = "update";
        $scope.formUrl = "includes/networks-form.html";
        $scope.formData = {
            attributes: []
        };


        $q.all([
            User.get({id: 0}).$promise,
            Network.get({siteId: siteId, id: networkId}).$promise,
            Change.query({
                siteId: siteId, limit: 10, offset: 0,
                resource_name: "Network", resource_id: networkId
            }).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.network = results[1];
            $scope.changes = results[2].data;
            $scope.formData = $scope.network.toForm();
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#updateNetworkModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Network"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#updateNetworkModal");
        });

        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.updateNetwork = function(){
            var network = $scope.network;
            network.updateFromForm($scope.formData);
            network.$update({siteId: siteId}, function(data){
                $route.reload();
            }, function(data){
                $scope.updateError = data.data.error;
            });
        };

        $scope.deleteNetwork = function(){
            $scope.network.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/networks");
            }, function(data){
                $scope.deleteError = data.data.error;
            });
        };


    });

    app.controller("DevicesController",
            function($scope, $location, $q, $routeParams,
                     User, Device, Attribute, pagerParams, Paginator) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = {};
        $scope.devices = [];
        $scope.paginator = null;
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $scope.formUrl = "includes/devices-form.html";
        $scope.formData = {
            attributes: []
        };

        var params = _.extend(pagerParams(), {
            siteId: siteId,
        });

        $q.all([
            User.get({id: 0}).$promise,
            Device.query(params).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.devices = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);


            $scope.paginator = new Paginator(results[1]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#createDeviceModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Device"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});

                $scope.formData.attributes = _.chain($scope.attributes)
                    .filter(function(value){
                        return value.display;
                    })
                    .sortBy(function(value){
                        return value.required ? 0 : 1;
                    })
                    .map(function(value){
                        return {
                            name: value.name
                        };
                    }).value();
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#createDeviceModal");
        });


        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.createDevice = function() {
            var device = Device.fromForm($scope.formData);
            device.$save({siteId: siteId}, function(device){
                $location.path("/sites/" + siteId + "/devices/" + device.id);
            }, function(data){
                $scope.error = data.data.error;
            });
        };

    });

    app.controller("DeviceController",
            function($scope, $route, $location, $q, $routeParams,
                     User, Device, Attribute, Change) {

        $scope.loading = true;
        $scope.user = {};
        $scope.device = {};
        $scope.attributes = {};
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        var siteId = $scope.siteId = $routeParams.siteId;
        var deviceId = $scope.deviceId = $routeParams.deviceId;
        $scope.formMode = "update";
        $scope.formUrl = "includes/devices-form.html";
        $scope.formData = {
            attributes: []
        };


        $q.all([
            User.get({id: 0}).$promise,
            Device.get({siteId: siteId, id: deviceId}).$promise,
            Change.query({
                siteId: siteId, limit: 10, offset: 0,
                resource_name: "Device", resource_id: deviceId
            }).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.device = results[1];
            $scope.changes = results[2].data;
            $scope.formData = $scope.device.toForm();
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#updateDeviceModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Device"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#updateDeviceModal");
        });

        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.updateDevice = function(){
            var device = $scope.device;
            device.updateFromForm($scope.formData);
            device.$update({siteId: siteId}, function(data){
                $route.reload();
            }, function(data){
                $scope.updateError = data.data.error;
            });
        };

        $scope.deleteDevice = function(){
            $scope.device.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/devices");
            }, function(data){
                $scope.deleteError = data.data.error;
            });
        };

    });

    app.controller("InterfacesController",
            function($scope, $location, $q, $routeParams,
                     User, Interface, Attribute, Device, pagerParams, Paginator) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = {};
        $scope.interfaces = [];
        $scope.devices = [];
        $scope.paginator = null;
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $scope.formMode = "create";
        $scope.formUrl = "includes/interfaces-form.html";
        $scope.formData = {
            attributes: [],
            devices: []
        };

        var params = _.extend(pagerParams(), {
            siteId: siteId,
        });

        $q.all([
            User.get({id: 0}).$promise,
            Interface.query(params).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.interfaces = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);


            $scope.paginator = new Paginator(results[1]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#createInterfaceModal", function(e){
            Device.query({siteId: siteId}, function(response){
                $scope.devices = response.data;
                $scope.formData.devices = _.chain($scope.devices).value();
                /*
                $scope.getDeviceById = _.reduce(
                        $scope.devices, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});

                $scope.formData.devices = _.chain($scope.devices).value();
                    .filter(function(value){
                        return value.display;
                    })
                    .sortBy(function(value){
                        return value.required ? 0 : 1;
                    })
                    .map(function(value){
                        return {
                            name: value.name
                        };
                    }).value();
                */
            });
        });

        $("body").on("show.bs.modal", "#createInterfaceModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Interface"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});

                $scope.formData.attributes = _.chain($scope.attributes)
                    .filter(function(value){
                        return value.display;
                    })
                    .sortBy(function(value){
                        return value.required ? 0 : 1;
                    })
                    .map(function(value){
                        return {
                            name: value.name
                        };
                    }).value();
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#createInterfaceModal");
        });


        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.createInterface = function() {
            var iface = Interface.fromForm($scope.formData);
            iface.$save({siteId: siteId}, function(iface){
                $location.path("/sites/" + siteId + "/interfaces/" + iface.id);
            }, function(data){
                $scope.error = data.data.error;
            });
        };

    });

    app.controller("InterfaceController",
            function($scope, $route, $location, $q, $routeParams,
                     Restangular, Users, Interface, Attribute, Change) {
                     // User, Interface, Attribute, Change) {

        $scope.loading = true;
        $scope.user = {};
        $scope.iface = {};
        $scope.schema = null;
        $scope.attributes = {};
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        var siteId = $scope.siteId = $routeParams.siteId;
        var ifaceId = $scope.ifaceId = $routeParams.ifaceId;
        $scope.formMode = "update";
        $scope.formUrl = "includes/interfaces-form.html";
        $scope.formData = {
            attributes: []
        };

        /*
        Restangular.extendModel('users', function(model) {
            model.isAdmin = function(siteId, permissions) {
                var user_permissions = this.permissions[siteId] || {};

                return _.any(user_permissions, function(value) {
                    return _.contains(permissions, value);
                });
            };
            return model;
        });
        */

        Restangular.extendModel('interfaces', function(model) {
            model.toForm = function() {
		return {
		    device: this.device,
		    name: this.name,
		    description: this.description,
		    addresses: this.addresses,
		    speed: this.speed,
		    type: this.type,
		    mac_address: this.mac_address,
		    attributes: _.map(_.cloneDeep(this.attributes), function(attrVal, attrKey){
			if (_.isArray(attrVal)) {
			    attrVal = _.map(attrVal, function(val) {
				return {text: val};
			    });
			}

			return {
			    name: attrKey,
			    value: attrVal
			};

		    })
		};
            };
            return model;
        });

        var Site = Restangular.one('sites', siteId);
        // Restangular.one('sites', siteId).one('users', 0),

        console.log(Users);

        $q.all([
            // User.get({id: 0}).$promise,
            // Interface.get({siteId: siteId, id: ifaceId}).$promise,
            // @USER: Restangular.one('users', 0).get(),
            Users.one(0).get(),
            Restangular.one('interfaces', ifaceId).get(),
            Interface.schema({siteId: siteId, id: ifaceId}).$promise,
            Change.query({
                siteId: siteId, limit: 10, offset: 0,
                resource_name: "Interface", resource_id: ifaceId
            }).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.iface = results[1];
            $scope.schema = results[2].schema;
            $scope.changes = results[3].data;
            $scope.formData = $scope.iface.toForm();
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#updateInterfaceModal", function(e){
            Attribute.query({siteId: siteId, resource_name: "Interface"}, function(response){
                $scope.attributes = response.data;
                $scope.attributesByName = _.reduce(
                        $scope.attributes, function(acc, value, key){
                    acc[value.name] = value;
                    return acc;
                }, {});
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#updateInterfaceModal");
        });

        $scope.addAttr = function() {
            $scope.formData.attributes.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formData.attributes.splice(idx, 1);
        };

        $scope.updateInterface = function(){
            var iface = $scope.iface;
            iface.updateFromForm($scope.formData);
            iface.$update({siteId: siteId}, function(data){
                $route.reload();
            }, function(data){
                $scope.updateError = data.data.error;
            });
        };

        $scope.deleteInterface = function(){
            $scope.iface.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/interfaces");
            }, function(data){
                $scope.deleteError = data.data.error;
            });
        };

    });

    app.controller("AttributesController",
            function($scope, $route, $location, $q, $routeParams,
                     User, Attribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = [];
        $scope.error = null;
        $scope.admin = false;
        $scope.formMode = "create";
        $scope.formUrl = "includes/attributes-form.html";
        $scope.formData = {};

        var siteId = $scope.siteId = $routeParams.siteId;

        $q.all([
            User.get({id: 0}).$promise,
            Attribute.query({siteId: siteId}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.attributes = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.createAttribute = function(){
            var attribute = Attribute.fromForm($scope.formData);
            attribute.$save({siteId: siteId}, function(attr){
                $location.path(
                    "/sites/" + siteId + "/attributes/" + attr.id
                );
            }, function(data){
                $scope.error = data.data.error;
            });
        };

    });

    app.controller("AttributeController",
            function($scope, $route, $location, $q, $routeParams,
                     User, Attribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attribute = null;
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        $scope.formMode = "update";
        $scope.formUrl = "includes/attributes-form.html";
        $scope.formData = {};

        var siteId = $scope.siteId = $routeParams.siteId;
        var attributeId = $scope.attributeId = $routeParams.attributeId;

        $q.all([
            User.get({id: 0}).$promise,
            Attribute.get({siteId: siteId, id: attributeId}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.attribute = results[1];
            $scope.formData = $scope.attribute.toForm();
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.updateAttribute = function(){
            $scope.attribute.updateFromForm($scope.formData);
            $scope.attribute.$update({siteId: siteId}, function(){
                $route.reload();
            }, function(data){
                $scope.updateError = data.data.error;
            });
        };

        $scope.deleteAttribute = function(){
            $scope.attribute.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/attributes");
            }, function(data){
                $scope.deleteError = data.data.error;
            });
        };

    });

    app.controller("ChangesController",
            function($scope, $location, $q, $routeParams, Change,
                     pagerParams, Paginator) {

        $scope.loading = true;
        $scope.changes = [];
        $scope.paginator = null;

        var siteId = $scope.siteId = $routeParams.siteId;
        var params = pagerParams();

        $q.all([
            Change.query(_.extend({siteId: siteId}, params)).$promise
        ]).then(function(results){
            $scope.changes = results[0].data;
            $scope.paginator = new Paginator(results[0]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

    });

    app.controller("ChangeController",
            function($scope, $location, $q, $routeParams, Change) {

        $scope.loading = true;
        $scope.change = null;

        var siteId = $scope.siteId = $routeParams.siteId;
        var changeId = $scope.changeId = $routeParams.changeId;

        $q.all([
            Change.get({siteId: siteId, id: changeId}).$promise
        ]).then(function(results){
            $scope.change = results[0];
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

    });

})();

