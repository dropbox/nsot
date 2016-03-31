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
    };

    nsot.Pager = function(previous, next, count, $location) {
        this.previous = previous;
        this.next = next;
        this.count = count;
        this.$location = $location;

        // Use an 'a' element as a URL parser. How novel.
        var parser = document.createElement('a');
        parser.href = (this.next || this.previous);  // This is a hack.

        // Given "search" params; parse them into an object.
        // Ref: https://css-tricks.com/snippets/jquery/get-query-params-object/
        this.parse_query_params = function(str) {
            /// I have no idea WTF this hackery even is. Kill me.
            return str.replace(/(^\?)/, '')
                .split("&")
                .map(function(n) {
                    return n = n.split("="), this[n[0]] = n[1], this
                }.bind({}))[0];
        }

        // Use pager_params to calculate limit/offset/pages, etc.
        var pager_params = this.parse_query_params(parser.search);
        var limit = parseInt(pager_params.limit);
        var offset = parseInt(pager_params.offset);

        this.page = ((offset + limit) / limit) - 1;  // Another hack
        this.numPages = Math.ceil(count / limit);
        this.limit = limit;
        this.offset = offset - limit;

        this.hasFirst = function(){
            return this.offset !== 0;
        };

        this.hasPrevious = function(){
            return this.offset !== 0;
        };

        this.hasNext = function(){
            return this.offset + this.limit < this.count;
        };

        this.hasLast = function(){
            return this.offset + this.limit < this.count;
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
