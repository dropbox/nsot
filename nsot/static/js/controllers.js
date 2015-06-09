(function() {
    "use strict";

    var app = angular.module("nsotApp");

    app.controller("navigationController", [
            "$scope", "$location",
            function($scope, $location) {

        $scope.siteId = null;
        $scope.$on('$routeChangeStart', function(next, current) {
            $scope.siteId = current.params.siteId;
        });

        $scope.isActive = function(str){
            var path = $location.path();
            return path === str;
        };

    }]);

    app.controller("IndexController", [
            "$location", "Site",
            function($location, Site) {

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
    }]);

    app.controller("ProfileController", [
            "User", "$location", "$q",
            function(User, $location, $q) {
        $q.all([
            User.get({id: 0}).$promise,
        ]).then(function(results){
            $location.path("/users/" + results[0].id);
        });

    }]);

    app.controller("SitesController", [
            "$scope", "$q", "$location", "Site", "User",
            function($scope, $q, $location, Site, User) {

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
    }]);

    app.controller("SiteController", [
            "$scope", "$route", "$location", "$q", "$routeParams", "Site", "User",
            function($scope, $route, $location, $q, $routeParams, Site, User) {

        $scope.loading = true;

        $scope.user = null;
        $scope.site = null;
        $scope.admin = false;

        $scope.updateError = null;
        $scope.deleteError = null;

        var siteId = $routeParams.siteId;

        $q.all([
            User.get({id: 0}).$promise,
            Site.get({id: siteId}).$promise,
        ]).then(function(results){
            $scope.user = results[0];
            $scope.site = results[1];
            $scope.admin = $scope.user.isAdmin(siteId, ["admin"]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
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

    }]);

    app.controller("UsersController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            function($scope, $route, $location, $q, $routeParams) {
        $scope.loading = true;
    }
    ]);

    app.controller("UserController", [
            "$scope", "$route", "$location", "$q", "$routeParams", "User",
            function($scope, $route, $location, $q, $routeParams, User) {

        $scope.loading = true;
        $scope.currentUser = null;
        $scope.profileUser = null;
        $scope.secret_key = null;
        var userId = $routeParams.userId;
        $scope.isSelf = false;

        $scope.showKey = function(){
            User.get({id: userId, with_secret_key: true}, function(data){
                $scope.secret_key = data.secret_key;
            });
        };

        $scope.rotateKey = function(){
            $scope.profileUser.rotateSecretKey().success(function(new_key){
                $scope.secret_key = new_key;
            });
        };

        $q.all([
            User.get({id: 0}).$promise,
            User.get({id: userId}).$promise,
        ]).then(function(results){
            $scope.loading = false;
            $scope.currentUser = results[0];
            $scope.profileUser = results[1];
            $scope.isSelf = $scope.currentUser.id === $scope.profileUser.id;
        });
    }]);

    app.controller("NetworksController", [
            "$scope", "$location", "$q", "$routeParams",
            "User", "Network", "Attribute", "pagerParams", "Paginator",
            function($scope, $location, $q, $routeParams,
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
        $scope.formUrl = "/static/templates/includes/networks-form.html";
        $scope.formData = {
            attributes: []
        };

        $scope.filters = {
            include_ips: nsot.qpBool($routeParams, "include_ips", true),
            include_networks: nsot.qpBool($routeParams, "include_networks", true),
            root_only: nsot.qpBool($routeParams, "root_only", false)
        }

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

    }
    ]);

    app.controller("NetworkController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "Network", "Attribute", "Change",
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
        $scope.formUrl = "/static/templates/includes/networks-form.html";
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


    }]);

    app.controller("DevicesController", [
            "$scope", "$location", "$q", "$routeParams",
            "User", "Device", "Attribute", "pagerParams", "Paginator",
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

        $scope.formUrl = "/static/templates/includes/devices-form.html";
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

    }
    ]);

    app.controller("DeviceController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "Device", "Attribute", "Change",
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
        $scope.formUrl = "/static/templates/includes/devices-form.html";
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


    }]);
    app.controller("AttributesController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "Attribute",
            function($scope, $route, $location, $q, $routeParams,
                     User, Attribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = [];
        $scope.error = null;
        $scope.admin = false;
        $scope.formMode = "create";
        $scope.formUrl = "/static/templates/includes/attributes-form.html";
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

    }
    ]);

    app.controller("AttributeController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "Attribute",
            function($scope, $route, $location, $q, $routeParams,
                     User, Attribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attribute = null;
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        $scope.formMode = "update";
        $scope.formUrl = "/static/templates/includes/attributes-form.html";
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

    }]);

    app.controller("ChangesController", [
            "$scope", "$location", "$q", "$routeParams", "Change",
            "pagerParams", "Paginator",
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

    }]);

    app.controller("ChangeController", [
            "$scope", "$location", "$q", "$routeParams", "Change",
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

    }]);

})();
