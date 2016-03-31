(function() {
    "use strict";

    var app = angular.module("nsotApp");

    function appendTransform(defaults, transform) {
        defaults = angular.isArray(defaults) ? defaults : [defaults];
        return defaults.concat(transform);
    }

    function buildActions($http, resourceName, collectionName) {

        // Return a single object
        var resourceTransform = appendTransform(
            $http.defaults.transformResponse, function(response) {
                return response;
            }
        );

        // Return a collection of objects
        var collectionTransform = appendTransform(
            $http.defaults.transformResponse, function(response) {
                if (response != undefined) {
                    return {
                        previous: response.previous,
                        next: response.next,
                        count: response.count,
                        data: response.results
                    };
                }
                return response;
            }
        );

        // Return the schema actions for a resource endpoint
        var schemaTransform = appendTransform(
            $http.defaults.transformResponse, function(response) {
                return {
                    schema: response.actions
                };
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
            },
            schema: {
                method: "OPTIONS", isArray: false,
                transformResponse: schemaTransform,
            }
        };
    }

    app.factory("Site", function($resource, $http){
        return $resource(
            "/api/sites/:id/",
            { id: "@id" },
            buildActions($http, "site", "sites")
        );
    });

    app.factory("User", function($resource, $http){
        var User = $resource(
            "/api/users/:id/",
            { id: "@id" },
            buildActions($http, "user", "users")
        );

        User.prototype.rotateSecretKey = function(){
            var userId = this.id;
            return $http({
                method: "POST",
                url: "/api/users/" + userId + "/rotate_secret_key/",
                data: {},
                transformResponse: appendTransform(
                    $http.defaults.transformResponse, function(response) {
                        return response.data.secret_key;
                    }
                )
            });
        };

        User.prototype.isAdmin = function(siteId, permissions){
            var user_permissions = this.permissions[siteId] || {};
                user_permissions = user_permissions.permissions || [];

            return _.any(user_permissions, function(value){
                return _.contains(permissions, value);
            });
        };

        return User;
    });

    app.factory("Change", function($resource, $http){
        return $resource(
            "/api/sites/:siteId/changes/:id/",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "change", "changes")
        );
    });

    app.factory("Attribute", function($resource, $http){
        var Attribute = $resource(
            "/api/sites/:siteId/attributes/:id/",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "attribute", "attributes")
        );

        Attribute.prototype.updateFromForm = function(formData) {
            return _.extend(this, {
                name: formData.name,
                resource_name: formData.resourceName,
                description: formData.description,
                required: formData.required,
                display: formData.display,
                multi: formData.multi,
                constraints: {
                    pattern: formData.pattern,
                    allow_empty: formData.allowEmpty,
                    valid_values: _.map(formData.validValues, function(value){
                        return value.text;
                    })
                }
            });
        };

        Attribute.fromForm = function(formData) {
            var attr = new Attribute();
            attr.updateFromForm(formData);
            return attr;
        };

        Attribute.prototype.toForm = function() {
            return {
                name: this.name,
                resourceName: this.resource_name,
                description: this.description,
                required: this.required,
                display: this.display,
                multi: this.multi,
                pattern: this.constraints.pattern,
                allowEmpty: this.constraints.allow_empty,
                validValues: _.map(this.constraints.valid_values, function(value) {
                    return { text: value };
                })
            };
        };

        return Attribute;
    });

    app.factory("Network", function($resource, $http){
        var Network = $resource(
            "/api/sites/:siteId/networks/:id/",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "network", "networks")
        );

        Network.prototype.updateFromForm = function(formData) {
            return _.extend(this, {
                cidr: formData.cidr,
                attributes: _.reduce(formData.attributes, function(acc, attribute){
                    if (!attribute.value) attribute.value = "";
                    if (_.isArray(attribute.value)) {
                        attribute.value = _.map(attribute.value, function(val){
                            return val.text;
                        });
                    }
                    acc[attribute.name] = attribute.value;
                    return acc;
                }, {})
            });
        };

        Network.fromForm = function(formData) {
            var network = new Network();
            network.updateFromForm(formData);
            return network;
        };

        Network.prototype.toForm = function() {
            return {
                cidr: this.network_address + "/" + this.prefix_length,
                attributes: _.map(_.cloneDeep(this.attributes), function(attrVal, attrKey){
                    if (_.isArray(attrVal)) {
                        attrVal = _.map(attrVal, function(val) {
                            return {text: val};
                        });
                    }

                    return {
                        name: attrKey,
                        value: attrVal
                    };

                })
            };
        };

        return Network;
    });

    app.factory("Device", function($resource, $http){
        var Device = $resource(
            "/api/sites/:siteId/devices/:id/",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "device", "devices")
        );

        Device.prototype.updateFromForm = function(formData) {
            return _.extend(this, {
                hostname: formData.hostname,
                attributes: _.reduce(formData.attributes, function(acc, attribute){
                    if (!attribute.value) attribute.value = "";
                    if (_.isArray(attribute.value)) {
                        attribute.value = _.map(attribute.value, function(val){
                            return val.text;
                        });
                    }
                    acc[attribute.name] = attribute.value;
                    return acc;
                }, {})
            });
        };

        Device.fromForm = function(formData) {
            var device = new Device();
            device.updateFromForm(formData);
            return device;
        };

        Device.prototype.toForm = function() {
            return {
                hostname: this.hostname,
                attributes: _.map(_.cloneDeep(this.attributes), function(attrVal, attrKey){
                    if (_.isArray(attrVal)) {
                        attrVal = _.map(attrVal, function(val) {
                            return {text: val};
                        });
                    }

                    return {
                        name: attrKey,
                        value: attrVal
                    };

                })
            };
        };

        return Device;
    });

    app.factory("Interface", function($resource, $http){
        var Interface = $resource(
            "/api/sites/:siteId/interfaces/:id/",
            { siteId: "@siteId", id: "@id" },
            buildActions($http, "interface", "interfaces")
        );

        Interface.prototype.updateFromForm = function(formData) {
            return _.extend(this, {
                device: formData.device,
                name: formData.name,
                description: formData.description,
                addresses: formData.addresses,
                speed: formData.speed,
                type: formData.type,
                mac_address: formData.mac_address,
                attributes: _.reduce(formData.attributes, function(acc, attribute){
                    if (!attribute.value) attribute.value = "";
                    if (_.isArray(attribute.value)) {
                        attribute.value = _.map(attribute.value, function(val){
                            return val.text;
                        });
                    }
                    acc[attribute.name] = attribute.value;
                    return acc;
                }, {})
            });
        };

        Interface.fromForm = function(formData) {
            var iface = new Interface();
            iface.updateFromForm(formData);
            return iface;
        };

        Interface.prototype.toForm = function() {
            return {
                device: this.device,
                name: this.name,
                description: this.description,
                addresses: this.addresses,
                speed: this.speed,
                type: this.type,
                mac_address: this.mac_address,
                attributes: _.map(_.cloneDeep(this.attributes), function(attrVal, attrKey){
                    if (_.isArray(attrVal)) {
                        attrVal = _.map(attrVal, function(val) {
                            return {text: val};
                        });
                    }

                    return {
                        name: attrKey,
                        value: attrVal
                    };

                })
            };
        };

        return Interface;
    });

    app.factory("pagerParams", function($location){

        var defaults = {
            limit: 10,
            offset: 0,
        };

        return function() {
            var params = _.clone(defaults);
            return _.extend(params, $location.search());
        };

    });

    app.factory("Paginator", function($location){
        return function(obj) {
            obj.limit = obj.data.length;  // Item count doubles as limit

            this.pager = new nsot.Pager(
                obj.previous,
                obj.next,
                obj.count,
                $location
            );
            this.limiter = new nsot.Limiter(
                obj.limit, $location
            );
        };
    });


})();
