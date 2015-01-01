(function() {

    app = angular.module("nsot", ["ngRoute"]);

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
    .config(function($routeProvider) {
        $routeProvider
        .when("/", {
            templateUrl: "/static/templates/index.html",
            controller: "IndexController"
        })
        .otherwise({redirectTo: "/"});
    });

    app.controller("IndexController", [
            "$scope", "$http", "$location",
            function($scope, $http, $location) {
        console.log("hello");
        $scope.hello = "Welcome to the Index page."

    }]);

})();
