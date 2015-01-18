(function() {
    "use strict";

    var app = angular.module("nsotApp");

    function appendTransform(defaults, transform) {
        defaults = angular.isArray(defaults) ? defaults : [defaults];
        return defaults.concat(transform);
    }

    function buildActions($http, resourceName, collectionName) {

        var resourceTransform = appendTransform(
            $http.defaults.transformResponse, function(response) {
                return response.data[resourceName];
            }
        );

        var collectionTransform = appendTransform(
            $http.defaults.transformResponse, function(response) {
                return {
                    limit: response.data.limit,
                    offset: response.data.offset,
                    total: response.data.total,
                    data: response.data[collectionName]
                }
            }
        );

        return {
            query:  {
                method: "GET", isArray: false,
                transformResponse: collectionTransform,
            },
            get: {
                method: "GET", isArray: false,
                transformResponse: resourceTransform,
            },
            update: {
                method: "PUT", isArray: false,
                transformResponse: resourceTransform,
            },
            save: {
                method: "POST", isArray: false,
                transformResponse: resourceTransform,
            }
        }
    }

    app.factory("Site", ["$resource", "$http", function($resource, $http){
        return $resource(
            "/api/sites/:id",
            { id: "@id" },
            buildActions($http, "site", "sites")
        );
    }]);

    app.factory("User", ["$resource", "$http", function($resource, $http){
        var User = $resource(
            "/api/users/:id",
            { id: "@id" },
            buildActions($http, "user", "users")
        );

        User.prototype.isAdmin = function(siteId, permissions){
            var user_permissions = this.permissions[siteId] || {};
                user_permissions = user_permissions.permissions || [];

            return _.any(user_permissions, function(value){
                return _.contains(permissions, value);
            });
        }

        return User;
    }]);

    app.factory("Change", ["$resource", "$http", function($resource, $http){
        return $resource(
            "/api/sites/:siteId/changes/:id",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "change", "changes")
        );
    }]);

    app.factory("NetworkAttribute", ["$resource", "$http", function($resource, $http){
        return $resource(
            "/api/sites/:siteId/network_attributes/:id",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "network_attribute", "network_attributes")
        );
    }]);

    app.factory("Network", ["$resource", "$http", function($resource, $http){
        return $resource(
            "/api/sites/:siteId/networks/:id",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "network", "networks")
        );
    }]);

    app.factory("pagerParams", ["$location", function($location){

        var defaults = {
            limit: 10,
            offset: 0,
        }

        return function() {
            var params = _.clone(defaults);
            return _.extend(params, $location.search());
        }

    }]);


    app.factory("Paginator", ["$location", function($location){
        return function(obj) {

            this.pager = new nsot.Pager(
                obj.offset,
                obj.limit,
                obj.total,
                $location
            );
            this.limiter = new nsot.Limiter(
                obj.limit, $location
            );
        }
    }]);


})();
