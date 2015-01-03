(function() {

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
        .when("/sites", {
            templateUrl: "/static/templates/sites.html",
            controller: "SitesController"
        })
        .when("/sites/:siteId", {
            templateUrl: "/static/templates/site.html",
            controller: "SiteController"
        })
        .otherwise({redirectTo: "/"});
    });

    app.controller("navigationController", [
            "$scope", "$location",
            function($scope, $location) {

        $scope.isActive = function(str){
            var path = $location.path();
            if (path.indexOf(str) === 0){
                return true;
            }
            return false;
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
            });
        };
    }]);

    app.controller("SiteController", [
            "$scope", "$http", "$q", "$routeParams",
            function($scope, $http, $q, $routeParams) {

        $scope.loading = true;
        $scope.user = {};
        $scope.site = {};

        $q.all([
            $http.get("/api/users/0"),
            $http.get("/api/sites/" + $routeParams.siteId)
        ]).then(function(results){
            $scope.user = results[0].data.data.user;
            $scope.site = results[1].data.data.site;
            $scope.loading = false;
        });

    }]);

})();
