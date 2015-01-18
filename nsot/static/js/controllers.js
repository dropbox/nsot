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
            "$scope", "$route", "$location", "$q", "$routeParams",
            function($scope, $route, $location, $q, $routeParams) {
        $scope.loading = true;
    }]);

    app.controller("NetworksController", [
            "$scope", "$location", "$q", "$routeParams",
            "User", "Network", "NetworkAttribute", "pagerParams", "Paginator",
            function($scope, $location, $q, $routeParams,
                     User, Network, NetworkAttribute, pagerParams, Paginator) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = {};
        $scope.networks = [];
        $scope.network = new Network();
        $scope.paginator = null;
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $scope.formMode = "create";
        $scope.formUrl = "/static/templates/includes/networks-form.html";
        $scope.formAttrs = [];

        var params = _.extend(pagerParams(), {
            siteId: siteId,
            include_ips: true
        });

        $q.all([
            User.get({id: 0}).$promise,
            Network.query(params).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.networks = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin", "networks"]);


            $scope.paginator = new Paginator(results[1]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#createNetworkModal", function(e){
            NetworkAttribute.query({siteId: siteId}, function(response){
                $scope.attributes = response.data;
            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#createNetworkModal");
        });


        $scope.addAttr = function() {
            $scope.formAttrs.push({});
        };

        $scope.removeAttr = function(idx) {
            $scope.formAttrs.splice(idx, 1);
        };

        $scope.createNetwork = function() {
            var network = $scope.network;
            var optional_attrs = _.reduce($scope.formAttrs, function(acc, value, key){
                acc[value.name] = value.value;
                return acc;
            }, {});

            _.defaults(network.attributes, optional_attrs);

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
            "User", "Network", "NetworkAttribute",
            function($scope, $route, $location, $q, $routeParams,
                     User, Network, NetworkAttribute) {

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
        $scope.formAttrs = [];


        $q.all([
            User.get({id: 0}).$promise,
            Network.get({siteId: siteId, id: networkId}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.network = results[1];
            $scope.admin = $scope.user.isAdmin(siteId, ["admin", "networks"]);

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $("body").on("show.bs.modal", "#updateNetworkModal", function(e){
            NetworkAttribute.query({siteId: siteId}, function(response){
                $scope.attributes = response.data;
                $scope.formAttrs = [];

                _.forEach($scope.attributes, function(value, idx){
                    if (!value.required && $scope.network.attributes[value.name]){
                        $scope.formAttrs.push({
                            name: value.name,
                            value: $scope.network.attributes[value.name]
                        });
                    }
                });

            });
        });

        $scope.$on('$destroy', function() {
            $("body").off("show.bs.modal", "#updateNetworkModal");
        });

        $scope.addAttr = function() {
            $scope.formAttrs.push({});
        };

        $scope.removeAttr = function(idx) {
            var attrName = $scope.formAttrs[idx].name;
            delete $scope.network.attributes[attrName];
            $scope.formAttrs.splice(idx, 1);
        };

        $scope.updateNetwork = function(){
            var network = $scope.network;
            var optional_attrs = _.reduce($scope.formAttrs, function(acc, value, key){
                acc[value.name] = value.value;
                return acc;
            }, {});

            _.extend(network.attributes, optional_attrs);

            $scope.network.$update({siteId: siteId}, function(data){
                $route.reload();
            }, function(data){
                $scope.updateError = data.error;
            });
        };

        $scope.deleteNetwork = function(){
            $scope.network.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/networks");
            }, function(data){
                $scope.deleteError = data.error;
            });
        };


    }]);

    app.controller("NetworkAttributesController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "NetworkAttribute",
            function($scope, $route, $location, $q, $routeParams,
                     User, NetworkAttribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attributes = [];
        $scope.attribute = new NetworkAttribute()
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $q.all([
            User.get({id: 0}).$promise,
            NetworkAttribute.query({siteId: siteId}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.attributes = results[1].data;
            $scope.admin = $scope.user.isAdmin(siteId, ["admin", "network_attrs"]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.createAttribute = function(){
            $scope.attribute.$save({siteId: siteId}, function(attr){
                $location.path(
                    "/sites/" + siteId + "/network_attributes/" + attr.id
                );
            }, function(data){
                $scope.error = data.error;
            });
        };

    }
    ]);

    app.controller("NetworkAttributeController", [
            "$scope", "$route", "$location", "$q", "$routeParams",
            "User", "NetworkAttribute",
            function($scope, $route, $location, $q, $routeParams,
                     User, NetworkAttribute) {

        $scope.loading = true;
        $scope.user = null;
        $scope.attribute = null;
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        var siteId = $scope.siteId = $routeParams.siteId;
        var attributeId = $scope.attributeId = $routeParams.networkAttributeId;


        $q.all([
            User.get({id: 0}).$promise,
            NetworkAttribute.get({siteId: siteId, id: attributeId}).$promise
        ]).then(function(results){
            $scope.user = results[0];
            $scope.attribute = results[1];
            $scope.admin = $scope.user.isAdmin(siteId, ["admin", "network_attrs"]);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.updateAttribute = function(){
            $scope.attribute.$update({siteId: siteId}, function(){
                $route.reload();
            }, function(data){
                $scope.updateError = data.error;
            });
        };

        $scope.deleteAttribute = function(){
            $scope.attribute.$delete({siteId: siteId}, function(){
                $location.path("/sites/" + siteId + "/network_attributes");
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
