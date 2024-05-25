window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
                return L.circleMarker(latlng, {
                    radius: 10,
                    fillColor: "#2C7BB2",
                    fillOpacity: 0.8
                }); // render a simple circle marker
            }

            ,
        function1: function(feature, latlng, index, context) {
            // Modify icon background color.
            const scatterIcon = L.DivIcon.extend({
                createIcon: function(oldIcon) {
                    let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
                    icon.style.backgroundColor = this.options.color;
                    return icon;
                }
            })
            // Render a circle with the number of leaves written in the center.
            const icon = new scatterIcon({
                html: '<div style="background-color:white;"><span>' + feature.properties.point_count_abbreviated + '</span></div>',
                className: "marker-cluster",
                iconSize: L.point(40, 40),
                color: "#2C7BB2"
            });
            return L.marker(latlng, {
                icon: icon
            })
        },
        function2: function(feature, latlng, context) {
            return L.circle(latlng, {
                radius: 200,
                fillColor: "#FB9500",
                color: "#FB9500",
                fillOpacity: 0.4
            }); // render a simple circle marker
        }

    }
});