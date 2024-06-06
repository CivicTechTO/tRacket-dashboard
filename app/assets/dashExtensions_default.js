window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
                return L.circle(latlng, {
                    radius: 25,
                    color: "#FB9500",
                    fillColor: "#FB9500",
                    fillOpacity: 0.4
                }); // render a simple circle marker
            }

            ,
        function1: function(feature, layer, context) {
            if (feature.properties.active) {
                {
                    var active = "<b>Active Location</b>";
                }
            } else {
                {
                    var active = "<b>Inactive Location</b>";
                }
            };
            if (feature.properties.label) {
                {
                    var label = feature.properties.label;
                }
            } else {
                {
                    var label = "";
                }
            };
            if (!feature.properties.cluster) {
                {
                    layer.bindTooltip(`${active}<br>${label}`)
                }
            };
        }
    }
});