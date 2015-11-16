(function() {
    "use strict";

    var templateCache = angular.module("nsotTemplates", []);
    var app = angular.module(
        "nsotApp",
        ["nsotTemplates", "ngRoute", "ngResource", "ngTagsInput", "chart.js"]
    );

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
            // Django expects a different CSRF header name than the default.
            // This will become configurable in Django 1.9.
            "xsrfHeaderName": "X-CSRFToken"
        });
    })
    // Tell Angular not to strip trailing slashes from URLs.
    .config(function($resourceProvider) {
        $resourceProvider.defaults.stripTrailingSlashes = false;
    })
    // Configure Chart.js global settings
    .config(function(ChartJsProvider) {
        // Override default colors for Pie charts.
        ChartJsProvider.setOptions('Pie', {
            colours: [
                "#dff0d8", // bg-success (green)
                "#d9edf7", // bg-info (blue)
                "#fcf8e3", // bg-warning (yellow)
                "#f2dede"  // bg-danger (red)
            ]
        });
    })
    // NSoT app routes.
    .config(function($routeProvider) {
        $routeProvider
        .when("/", {
            templateUrl: "index.html",
            controller: "IndexController"
        })
        .when("/users", {
            templateUrl: "users.html",
            controller: "UsersController"
        })
        .when("/users/:userId", {
            templateUrl: "user.html",
            controller: "UserController"
        })
        .when("/profile", {
            template: "",
            controller: "ProfileController"
        })
        .when("/sites", {
            templateUrl: "sites.html",
            controller: "SitesController"
        })
        .when("/sites/:siteId", {
            templateUrl: "site.html",
            controller: "SiteController"
        })
        .when("/sites/:siteId/networks", {
            templateUrl: "networks.html",
            controller: "NetworksController"
        })
        .when("/sites/:siteId/networks/:networkId", {
            templateUrl: "network.html",
            controller: "NetworkController"
        })
        .when("/sites/:siteId/devices", {
            templateUrl: "devices.html",
            controller: "DevicesController"
        })
        .when("/sites/:siteId/devices/:deviceId", {
            templateUrl: "device.html",
            controller: "DeviceController"
        })
        .when("/sites/:siteId/attributes", {
            templateUrl: "attributes.html",
            controller: "AttributesController"
        })
        .when("/sites/:siteId/attributes/:attributeId", {
            templateUrl: "attribute.html",
            controller: "AttributeController"
        })
        .when("/sites/:siteId/changes", {
            templateUrl: "changes.html",
            controller: "ChangesController"
        })
        .when("/sites/:siteId/changes/:changeId", {
            templateUrl: "change.html",
            controller: "ChangeController"
        })
        .otherwise({redirectTo: "/"});
    });

    app.run(function($rootScope){
        $rootScope.NSOT_VERSION = window.NSOT_VERSION;
    });


})();
