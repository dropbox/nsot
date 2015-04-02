(function() {
    "use strict";

    var app = angular.module("nsotApp", ["ngRoute", "ngResource", "ngTagsInput"]);

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
        .when("/profile", {
            template: "",
            controller: "ProfileController"
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
        .when("/sites/:siteId/devices", {
            templateUrl: "/static/templates/devices.html",
            controller: "DevicesController"
        })
        .when("/sites/:siteId/devices/:deviceId", {
            templateUrl: "/static/templates/device.html",
            controller: "DeviceController"
        })
        .when("/sites/:siteId/attributes", {
            templateUrl: "/static/templates/attributes.html",
            controller: "AttributesController"
        })
        .when("/sites/:siteId/attributes/:attributeId", {
            templateUrl: "/static/templates/attribute.html",
            controller: "AttributeController"
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

    app.run(["$rootScope", function($rootScope){
        $rootScope.NSOT_VERSION = window.NSOT_VERSION;
    }]);



})();
