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

    app.controller("navigationController", [
            "$scope", "$location",
            function($scope, $location) {

        $scope.siteId = null;
        $scope.$on('$routeChangeStart', function(next, current) {
            $scope.siteId = current.params.siteId;
        });

        $scope.isActive = function(str){
            var path = $location.path();
            return path === str
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
        $scope.updateError = null;
        $scope.deleteError = null;


        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + $routeParams.siteId)
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.site = results[1].data.data.site;
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
                console.log(data);
                $scope.error = data.error;
            });
        };

        $scope.deleteSite = function(site){
            $http.delete("/api/sites/" +  $routeParams.siteId, site).success(function(data){
                $location.path("/sites");
            }).error(function(data){
                $scope.error = data.error;
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

    }
    ]);

    app.controller("NetworkAttributeController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }]);

    app.controller("ChangesController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }
    ]);

    app.controller("ChangeController", [
            "$scope", "$http", "$route", "$location", "$q", "$routeParams",
            function($scope, $http, $route, $location, $q, $routeParams) {

        $scope.loading = true;

    }]);

})();
