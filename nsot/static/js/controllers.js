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
            "$http", "$location",
            function($http, $location) {

        $http.get("/api/sites").success(function(data){
            var sites = data.data.sites;
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
            "$scope", "$http", "$q", "$location",
            function($scope, $http, $q, $location) {

        $scope.loading = true;
        $scope.user = {};
        $scope.sites = [];
        $scope.site = {};
        $scope.error = null;

        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites")
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.sites = results[1].data.data.sites;
            $scope.loading = false;
        });

        $scope.createSite = function(site){
            $http.post("/api/sites", site).success(function(data){
                var site = data.data.site;
                $location.path("/sites/" + site.id);
            }).error(function(data){
                $scope.error = data.error;
            });
        };
    }]);

    app.controller("SiteController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.user = {};
        $scope.site = {};
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;


        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + $routeParams.siteId)
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.site = results[1].data.data.site;
            var permissions = $scope.user.permissions[$routeParams.siteId] || {};
            permissions = permissions.permissions || [];
            $scope.admin = _.any(permissions, function(value){
                return _.contains(["admin"], value);
            });

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.updateSite = function(site){
            $http.put("/api/sites/" + $routeParams.siteId, site).success(function(data){
                $route.reload();
            }).error(function(data){
                $scope.updateError = data.error;
            });
        };

        $scope.deleteSite = function(site){
            $http.delete("/api/sites/" +  $routeParams.siteId, site).success(function(data){
                $location.path("/sites");
            }).error(function(data){
                $scope.deleteError = data.error;
            });
        };

    }]);

    app.controller("UsersController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }
    ]);

    app.controller("UserController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }]);

    app.controller("NetworksController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.user = {};
        $scope.networks = [];
        $scope.network = {};
        $scope.attributes = {};
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;
        $scope.pager = null;
        $scope.limier = null;

        $scope.form_attrs = [];

        var params = {limit: 10, include_ips: true};
        var search = $location.search();
        if (search.offset) params.offset = search.offset;
        if (search.limit) params.limit = search.limit;

        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + siteId + "/network_attributes"),
            $http.get("/api/sites/" + siteId + "/networks", {
                params: params
            })
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.attributes = results[1].data.data.network_attributes;
            var data = results[2].data.data;
            $scope.networks = data.networks;

            var permissions = $scope.user.permissions[siteId] || {};
            permissions = permissions.permissions || [];
            $scope.admin = _.any(permissions, function(value){
                return _.contains(["admin", "networks"], value);
            });

            $scope.pager = new nsot.Pager(
                data.offset, data.limit, data.total, $location
            );
            $scope.limiter = new nsot.Limiter(data.limit, $location);

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.addAttr = function(idx) {
            $scope.form_attrs.splice(idx + 1, 0, {});
        }

        $scope.removeAttr = function(idx) {
            $scope.form_attrs.splice(idx, 1);
        }

        $scope.createNetwork = function() {
            var network = $scope.network;
            var optional_attrs = _.reduce($scope.form_attrs, function(acc, value, key){
                acc[value.name] = value.value;
                return acc;
            }, {});

            _.defaults(network.attributes, optional_attrs);

            $http.post("/api/sites/" + siteId +
                       "/networks", network).success(function(data){
                network = data.data.network;
                $location.path("/sites/" + siteId + "/networks/" + network.id);
            }).error(function(data){
                $scope.error = data.error;
            });
        };

    }
    ]);

    app.controller("NetworkController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }]);

    app.controller("NetworkAttributesController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.user = {};
        $scope.attributes = [];
        $scope.attribute = {};
        $scope.error = null;
        $scope.admin = false;
        var siteId = $scope.siteId = $routeParams.siteId;

        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + siteId + "/network_attributes")
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.attributes = results[1].data.data.network_attributes;
            var permissions = $scope.user.permissions[$routeParams.siteId] || {};
            permissions = permissions.permissions || [];
            $scope.admin = _.any(permissions, function(value){
                return _.contains(["admin", "network_attrs"], value);
            });
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.createAttribute = function(attr){
            $http.post("/api/sites/" + siteId +
                       "/network_attributes", attr).success(function(data){
                var attr = data.data.network_attribute;
                $location.path("/sites/" + siteId + "/network_attributes/" + attr.id);
            }).error(function(data){
                $scope.error = data.error;
            });
        };

    }
    ]);

    app.controller("NetworkAttributeController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.user = {};
        $scope.attribute = {};
        $scope.admin = false;
        $scope.updateError = null;
        $scope.deleteError = null;
        var siteId = $scope.siteId = $routeParams.siteId;
        var attributeId = $scope.attributeId = $routeParams.networkAttributeId;


        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + siteId + "/network_attributes/" + attributeId)
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.attribute = results[1].data.data.network_attribute;
            var permissions = $scope.user.permissions[$routeParams.siteId] || {};
            permissions = permissions.permissions || [];
            $scope.admin = _.any(permissions, function(value){
                return _.contains(["admin", "network_attrs"], value);
            });

            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

        $scope.updateAttribute = function(attr){
            $http.put("/api/sites/" + siteId +
                      "/network_attributes/" + attributeId, attr).success(function(data){
                $route.reload();
            }).error(function(data){
                $scope.updateError = data.error;
            });
        };

        $scope.deleteAttribute = function(attr){
            $http.delete("/api/sites/" + siteId +
                      "/network_attributes/" + attributeId).success(function(data){
                $location.path("/sites/" + siteId + "/network_attributes");
            }).error(function(data){
                $scope.deleteError = data.error;
            });
        };

    }]);

    app.controller("ChangesController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.changes = [];
        $scope.siteId = $routeParams.siteId;
        $scope.pager = null;
        $scope.limier = null;

        var params = {limit: 10};
        var search = $location.search();
        if (search.offset) params.offset = search.offset;
        if (search.limit) params.limit = search.limit;

        $q.all([
            $http.get(
                "/api/sites/" + $scope.siteId +
                "/changes",
                {params: params}
            )
        ]).then(function(results){
            var data = results[0].data.data;
            $scope.changes = data.changes;
            $scope.pager = new nsot.Pager(
                data.offset, data.limit, data.total, $location
            );
            $scope.limiter = new nsot.Limiter(data.limit, $location);
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

    }]);

    app.controller("ChangeController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;
        $scope.change = {};
        $scope.siteId = $routeParams.siteId;

        $q.all([
            $http.get(
                "/api/sites/" + $scope.siteId +
                "/changes/" + $routeParams.changeId
            )
        ]).then(function(results){
            $scope.change = results[0].data.data.change;
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

    }]);

})();
