define([
    "dojo/_base/declare",
    "./_Base"
], function (
    declare,
    _Base
) {
    return declare([_Base], {
        olLayerClassName: "layer.VectorTile",
        olSourceClassName: "source.VectorTile",

        constructor: function(name, loptions, soptions) {
            this.inherited(arguments);
        }
    });
});
