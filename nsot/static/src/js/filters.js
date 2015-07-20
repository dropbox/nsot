(function() {
    "use strict";

    var app = angular.module("nsotApp");

    app.filter("from_now", function(){
        return function(input){
            return moment.unix(input).fromNow();
        };
    });

    app.filter("ts_fmt", function(){
        return function(input){
            return moment.unix(input).format("YYYY/MM/DD hh:mm:ss a");
        };
    });

})();
