var LinkShim = {
    // Configuration options
    redirect_url: "http://localhost:8888/r?",
    tracker_attr: "data-track",
    params: {},

    changeHref: function(a) {
        var $a = $(a);
        var params = this.params;
        var url = this.redirect_url;

        // Add any tracking attributes to the URL
        var trackData = $a.attr(this.tracker_attr);
        if (trackData) {
            url += trackData + "&";
        }

        // Build params                    
        params.href = $a.attr('href');
        for (var f in params) {
            url += f + "=" + encodeURIComponent(params[f]) + "&";
        }

        // Trim the trailing '&' and set the new URL
        url = url.slice(0, -1);
        $a.attr('href', url);
    },

    // Manually call to add PageParams
    addPageParams: function(new_params) {
        if (typeof new_params == 'object') {
            for (var f in new_params) {
                this.params[f] = new_params[f];
            }
        }
    },

    // Call to listen to clicks on objects that contain the tracker_attr
    init: function() {
        var obj = this;
        $("a[" + obj.tracker_attr + "]").on('click', function(e) {
            e.preventDefault();
            obj.changeHref(this);
            window.location = $(this).attr('href');
        });
    }
};
