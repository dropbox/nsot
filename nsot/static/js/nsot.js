(function() {
    "use strict";

    var nsot = window.nsot = nsot || {};
    var TRUTHY = ["true", "yes", "on", "1", ""];

    nsot.qpBool = function(object, path, defaultValue) {
        var val = _.get(object, path, defaultValue).toString().toLowerCase();
        for (var idx = 0; idx < TRUTHY.length; idx++) {
            var elem = TRUTHY[idx];
            if (val === elem) {
                return true;
            }
        }
        return false;
    }

    nsot.Pager = function(offset, limit, total, $location) {
        this.offset = offset;
        this.limit = limit;
        this.total = total;
        this.$location = $location;

        this.page = (offset + limit) / limit;
        this.numPages = Math.ceil(total/limit);

        this.hasFirst = function(){
            return this.offset !== 0;
        };

        this.hasPrevious = function(){
            return this.offset !== 0;
        };

        this.hasNext = function(){
            return this.offset + this.limit < this.total;
        };

        this.hasLast = function(){
            return this.offset + this.limit < this.total;
        };

        this.firstPage = function(){
            return 0;
        };

        this.previousPage = function(){
            return this.offset - this.limit;
        };

        this.nextPage = function(){
            return this.offset + this.limit;
        };

        this.lastPage = function(){
            return (this.numPages - 1) * this.limit;
        };

        this.firstPageUrl = function(){
            return "?" + $.param(_.defaults(
                {"offset": this.firstPage()},
                this.$location.search()
            ));
        };

        this.previousPageUrl = function(){
            return "?" + $.param(_.defaults(
                {"offset": this.previousPage()},
                this.$location.search()
            ));
        };

        this.nextPageUrl = function(){
            return "?" + $.param(_.defaults(
                {"offset": this.nextPage()},
                this.$location.search()
            ));
        };

        this.lastPageUrl = function(){
            return "?" + $.param(_.defaults(
                {"offset": this.lastPage()},
                this.$location.search()
            ));
        };
    };

    nsot.Limiter = function(limit, $location) {

        this.name = "Limit";
        this.current = limit;
        this.values = [10, 25, 50, 100];
        this.$location = $location;

        this.getUrl = function(value){
            return "?" + $.param(_.defaults(
                {"limit": value}, this.$location.search()
            ));
        };
    };

})();
