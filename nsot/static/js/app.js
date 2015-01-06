(function() {
    "use strict";

    var app = angular.module("nsotApp", ["ngRoute"]);

    app.config(function($interpolateProvider){
        $interpolateProvider.startSymbol("[[");
        $interpolateProvider.endSymbol("]]");
    })
    .config(function($logProvider){
        $logProvider.debugEnabled(true);
    })
    .config(function($locationProvider) {
        $locationProvider.html5Mode({
            enabled: true,
            requireBase: false
        });
    })
    .config(function($httpProvider) {
        _.assign($httpProvider.defaults, {
            "xsrfCookieName": "_xsrf",
            "xsrfHeaderName": "X-XSRFToken"
        });
    })
    .config(function($routeProvider) {
        $routeProvider
        .when("/", {
            templateUrl: "/static/templates/index.html",
            controller: "IndexController"
        })
        .when("/users", {
            templateUrl: "/static/templates/users.html",
            controller: "UsersController"
        })
        .when("/users/:userId", {
            templateUrl: "/static/templates/user.html",
            controller: "UserController"
        })
        .when("/sites", {
            templateUrl: "/static/templates/sites.html",
            controller: "SitesController"
        })
        .when("/sites/:siteId", {
            templateUrl: "/static/templates/site.html",
            controller: "SiteController"
        })
        .when("/sites/:siteId/networks", {
            templateUrl: "/static/templates/networks.html",
            controller: "NetworksController"
        })
        .when("/sites/:siteId/networks/:networkId", {
            templateUrl: "/static/templates/network.html",
            controller: "NetworkController"
        })
        .when("/sites/:siteId/network_attributes", {
            templateUrl: "/static/templates/network-attributes.html",
            controller: "NetworkAttributesController"
        })
        .when("/sites/:siteId/network_attributes/:networkAttributeId", {
            templateUrl: "/static/templates/network-attribute.html",
            controller: "NetworkAttributeController"
        })
        .when("/sites/:siteId/changes", {
            templateUrl: "/static/templates/changes.html",
            controller: "ChangesController"
        })
        .when("/sites/:siteId/changes/:changeId", {
            templateUrl: "/static/templates/change.html",
            controller: "ChangeController"
        })
        .otherwise({redirectTo: "/"});
    });

    app.filter("from_now", function(){
        return function(input){
            return moment.unix(input).fromNow();
        };
    });

    app.filter("ts_fmt", function(){
        return function(input){
            return moment.unix(input).format("YYYY/MM/DD hh:mm:ss a");
        };
    });

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

        $q.all([
            $http.get(
                "/api/sites/" + $scope.siteId +
                "/changes"
            )
        ]).then(function(results){
            $scope.changes = results[0].data.data.changes;
            $scope.loading = false;
        }, function(data){
            if (data.status === 404) {
                $location.path("/");
                $location.replace();
            }
        });

    }
    ]);

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
