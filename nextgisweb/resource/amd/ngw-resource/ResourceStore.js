/* globals define */
define([
    "dojo/_base/declare",
    "dojo/store/JsonRest",
    "ngw/route"
], function (
    declare,
    JsonRest,
    route
) {
    return declare("ngw.resource.ResourceStore", [JsonRest], {
        target: route.resource.store({id: ""}),
        headers: { "Accept": "application/json" },
        getChildren: function(object){
            return this.query({parent_id: object.id}).filter(function (itm) {
                if (!itm.children) {
                    if (this.resCls && (this.resCls !== itm.cls)) { return false; }
                    if (this.resIface && itm.interfaces.indexOf(this.resIface) == -1) { return false; }
                }
                return true;
            }, this);
        }
    });
});
