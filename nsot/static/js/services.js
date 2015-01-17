(function() {
    "use strict";

    var app = angular.module("nsotApp");

    var actions = {
        query:  {
            method: "GET", isArray: false
        },
        update: {
            method: "PUT"
        }
    };

    app.factory("Site", ["$resource", function($resource){
        return $resource("/api/sites/:id", { id: "@id" }, actions);
    }]);

    app.factory("User", ["$resource", function($resource){
        return $resource("/api/users/:id", { id: "@id" }, actions);
    }]);

    app.factory("Change", ["$resource", function($resource){
        return $resource(
            "/api/sites/:siteId/changes/:id",
            { siteId: "@siteId", id: "@id" },
            actions
        );
    }]);

    app.factory("NetworkAttribute", ["$resource", function($resource){
        return $resource(
            "/api/sites/:siteId/network_attributes/:id",
            { siteId: "@siteId", id: "@id" },
            actions
        );
    }]);

    app.factory("Network", ["$resource", function($resource){
        return $resource(
            "/api/sites/:siteId/networks/:id",
            { siteId: "@siteId", id: "@id" },
            actions
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
            this.pager = new nsot.Pager(obj.offset, obj.limit, obj.total, $location);
            this.limiter = new nsot.Limiter(obj.limit, $location);
        }
    }]);


})();
