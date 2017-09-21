/* global define */
define([
    "dojo/_base/declare",
    "./Adapter",
    "ngw/route",
    "ngw/openlayers/layer/VectorTile",
    "openlayers/ol"
], function (declare, Adapter, route, VectorTile, ol) {
    return declare(Adapter, {
        createLayer: function (item) {
            return new VectorTile(item.id, {
                visible: item.visibility,
                maxResolution: item.maxResolution ? item.maxResolution : undefined,
                minResolution: item.minResolution ? item.minResolution : undefined,
                opacity: item.transparency ? (1 - item.transparency / 100) : 1.0
            }, {
                format: new ol.format.MVT(),
                tileGrid: ol.tilegrid.createXYZ(),
                tilePixelRatio: 16,
                wrapX: false,
                url: route.feature_layer.mvt(item.layerId, '{z}', '{x}', '{y}')
            });
    }});
});
