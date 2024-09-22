window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, layer, context) {
            if (feature.properties.sending_data) {
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
        },
        function1: function(feature, latlng, context) {
                if (feature.properties.sending_data) {
                    var color = "#FB9500";
                } else {
                    var color = "#545454";
                };
                return L.circleMarker(latlng, {
                    radius: 10,
                    fillColor: color,
                    fillOpacity: 0.8,
                }); // render a simple circle marker
            }

            ,
        function2: function(feature, latlng, index, context) {
            // Modify icon background color.
            const scatterIcon = L.DivIcon.extend({
                createIcon: function(oldIcon) {
                    let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
                    icon.style.backgroundColor = this.options.color;
                    return icon;
                }
            })
            const leaves = index.getLeaves(feature.properties.cluster_id);
            var cluster_color = "#545454";
            for (let i = 0; i < leaves.length; ++i) {
                if (leaves[i].properties.sending_data) {
                    var cluster_color = "#FB9500";
                }
            }
            // Render a circle with the number of leaves written in the center.
            const icon = new scatterIcon({
                html: '<div style="background-color:white;"><span>' + feature.properties.point_count_abbreviated + '</span></div>',
                className: "marker-cluster",
                iconSize: L.point(40, 40),
                color: cluster_color
            });
            return L.marker(latlng, {
                icon: icon
            })
        },
        function3: function(feature, latlng, context) {
            return L.circle(latlng, {
                radius: context.hideout["radius"],
                color: context.hideout["color"],
                fillColor: context.hideout["color"],
                fillOpacity: 0.4
            }); // render a simple circle marker
        }

    }
});