/* global define, console */
define([
    "dojo/_base/declare",
    "dojo/_base/array",
    "dojo/_base/lang",
    "dojo/aspect",
    "dojo/request/xhr",
    "dijit/layout/ContentPane",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "ngw/route",
    "ngw-pyramid/i18n!wfsclient",
    "ngw-pyramid/hbs-i18n",
    "ngw-resource/serialize",
    // resource
    "dojo/text!./template/LayerWidget.hbs",
    // template
    "dijit/form/ComboBox",
    "dijit/layout/BorderContainer",
    "dojox/layout/TableContainer",
    "ngw-spatial-ref-sys/SpatialRefSysSelect",
    "ngw-resource/ResourceBox",
    "ngw-resource/ResourcePicker"
], function (
    declare,
    array,
    lang,
    aspect,
    xhr,
    ContentPane,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    route,
    i18n,
    i18nHbs,
    serialize,
    template
) {
    return declare([ContentPane, serialize.Mixin, _TemplatedMixin, _WidgetsInTemplateMixin], {
        title: i18n.gettext("WFS layer"),
        templateString: i18nHbs(template, i18n),
        serializePrefix: "wfsclient_layer",

        postCreate: function () {
            this.inherited(arguments);

            this.wSRS.set("disabled", this.composite.operation !== "create");
            this.wFields.set("value", this.composite.operation == "create" ? "update" : "keep");

            aspect.after(this.wConnection, "set", lang.hitch(this, function (name, value) {
                if (name == "value") { this.loadCapCache(value); }
            }), true);
        },

        loadCapCache: function (connection) {
            var widget = this,
                tnStore = this.wTypeName.store;

            var render = function (capdata) {
                tnStore.query().forEach(function (layer) {
                    tnStore.remove(layer.id);
                });
                array.forEach(capdata.layers, function (layer) {
                    widget.wTypeName.get("store").add({
                        id: layer.id, name: layer.id
                    });
                });
            };

            if (connection !== null) {
                this.wConnection.store.get(connection.id).then(function (data) {
                    xhr.get(route.resource.item(data.id),{
                        handleAs: "json"
                    }).then(function (data) {
                        render(data.wfsclient_connection.capcache);
                    });
                });
            }
        },
        
        serializeInMixin: function (data) {
            if (data[this.serializePrefix] === undefined) { data[this.serializePrefix] = {}; }
            var value = data[this.serializePrefix];

            value.connection = this.wConnection.get("value");
            value.srs = {id: this.wSRS.get("value")};
            value.typename = this.wTypeName.get("value");
        },

        deserializeInMixin: function (data) {
            var value = data[this.serializePrefix];
            if (value === undefined) { return; }

            this.wConnection.set("value", value.connection);
            this.wSRS.set("value", value.srs.id);
            this.wTypeName.set("value", value.typename);
        }
    });
});
