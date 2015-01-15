(function() {
    "use strict";

    var app = angular.module("nsotApp");

    app.factory("Site", ["$resource", function($resource){
        return $resource("/api/sites/:id", { id: "@id" }, {
            query:  {
                method: "GET", isArray: true,
                transformResponse: function(data){
                    data = angular.fromJson(data);
                    return data.data.sites;
                }
            },
            get:  {
                method: "GET",
                transformResponse: function(data){
                    data = angular.fromJson(data);
                    return data.data.site;
                }
            },
            update: { method: "PUT" }
        });
    }]);

    app.factory("User", ["$resource", function($resource){
        return $resource("/api/users/:id", { id: "@id" }, {
            query:  {
                method: "GET", isArray: true,
                transformResponse: function(data){
                    data = angular.fromJson(data);
                    return data.data.users;
                }
            },
            get:  {
                method: "GET",
                transformResponse: function(data){
                    data = angular.fromJson(data);
                    return data.data.user;
                }
            },
            update: { method: "PUT" }
        });
    }]);

})();
