(function() {
    "use strict";

    var app = angular.module("nsotApp");

    app.directive("panel", function(){
        return {
            restrict: "E",
            transclude: true,
            template: "<div class='panel panel-default'>" +
                      "  <ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });

    app.directive("panelHeading", function(){
        return {
            restrict: "E",
            transclude: true,
            template: "<div class='panel-heading'><strong>" +
                      "  <ng-transclude></ng-transclude>" +
                      "</strong></div>"
        };
    });

    app.directive("panelBody", function(){
        return {
            restrict: "E",
            transclude: true,
            template: "<div class='panel-body'>" +
                      "  <ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });

    app.directive("panelFooter", function(){
        return {
            restrict: "E",
            transclude: true,
            template: "<div class='panel-footer'>" +
                      "  <ng-transclude></ng-transclude>" +
                      "</div>"
        };
    });

    app.directive("loadingPanel", function(){
        return {
            restrict: "E",
            templateUrl: "/static/templates/directives/loading-panel.html"
        };
    });

    app.directive("headingBar", function(){
        return {
            restrict: "E",
            scope: {
                "heading": "@",
                "subheading": "@"
            },
            transclude: true,
            template: "<div class='row'><div class='col-md-12'>" +
                      "  <div class='header'>" +
                      "    <h2>[[heading]]</h2>" +
                      "    <h3 ng-if='subheading'>[[subheading]]</h3>" +
                      "    <div class='buttons'>" +
                      "      <ng-transclude></ng-transclude>" +
                      "    </div>" +
                      "  </div>" +
                      "</div></div>"
        };
    });

    app.directive("nsotModal", function(){
        return {
            restrict: "E",
            scope: {
                "title": "@",
                "modalId": "@",
                "modalSize": "@"
            },
            transclude: true,
            templateUrl: "/static/templates/directives/nsot-modal.html"
        };
    });

    app.directive("paginator", function(){
        return {
            restrict: "E",
            scope: {
                "pager": "=",
            },
            templateUrl: "/static/templates/directives/paginator.html"
        };
    });

    app.directive("dropdown", function(){
        return {
            restrict: "E",
            scope: {
                "ctxtObj": "=",
            },
            templateUrl: "/static/templates/directives/dropdown.html"
        };
    });

})();
