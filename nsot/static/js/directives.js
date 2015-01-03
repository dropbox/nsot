(function() {

    var app = angular.module("nsotApp");

    app.directive("panel", function(){
        return {
            restrict: "E",
            transclude: true,
            replace: true,
            template: "<div class='panel panel-default'>" +
                      "<ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });

    app.directive("panelHeading", function(){
        return {
            restrict: "E",
            transclude: true,
            replace: true,
            template: "<div class='panel-heading'><strong>" +
                      "<ng-transclude></ng-transclude>" +
                      "</strong></div>"
        };
    });

    app.directive("panelBody", function(){
        return {
            restrict: "E",
            transclude: true,
            replace: true,
            template: "<div class='panel-body'>" +
                      "<ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });

    app.directive("panelFooter", function(){
        return {
            restrict: "E",
            transclude: true,
            replace: true,
            template: "<div class='panel-footer'>" +
                      "<ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });


    app.directive("loadingPanel", function(){
        return {
            restrict: "E",
            templateUrl: "/static/templates/directives/loading-panel.html"
        };
    });

})();
