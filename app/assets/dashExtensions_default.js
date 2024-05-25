window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng, context) {
                if (feature.properties.active === 1) {
                    console.log("active")
                    var color = "#FB9500";
                    var opcaity = 0.8;
                } else {
                    var color = "#545454";
                    var opacity = 0.4;
                };
                return L.circleMarker(latlng, {
                    radius: 10,
                    fillColor: color,
                    fillOpacity: opacity,
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
                color: "#FB9500"
            });
            return L.marker(latlng, {
                icon: icon
            })
        }
    }
});