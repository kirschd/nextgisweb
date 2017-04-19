define([
    "dojo/_base/declare",
    "dojo/_base/array",
    "dojo/_base/lang",
    "dojo/json",
    "dojo/store/Memory",
    "dojo/request/xhr",
    "dojo/dom-style",
    "dijit/Dialog",
    "dijit/_WidgetsInTemplateMixin",
    "ngw-pyramid/i18n!feature_layer",
    "ngw-pyramid/hbs-i18n",
    "ngw/route",
    "ngw/settings!feature_layer",
    "dojo/text!./template/FeatureAttributeFilterActionBar.hbs",
    "dojox/layout/TableContainer",
    "dojox/form/CheckedMultiSelect",
    "dijit/form/Select",
    // template
    "dijit/form/Button",
    // css
    "xstyle/css!" + ngwConfig.amdUrl + "dojox/form/resources/CheckedMultiSelect.css"
], function (
    declare,
    array,
    lang,
    json,
    Memory,
    xhr,
    domStyle,
    Dialog,
    _WidgetsInTemplateMixin,
    i18n,
    hbsI18n,
    route,
    settings,
    actionBarMarkup,
    TableContainer,
    CheckedMultiSelect,
    Select
) {
    return declare([Dialog, _WidgetsInTemplateMixin], {
        title: i18n.gettext("Filter by attributes"),
        actionBarTemplate: hbsI18n(actionBarMarkup, i18n),

        buildRendering: function () {
            this.inherited(arguments);

            this.container = new TableContainer({
                cols: 1,
                style: "width: 400px"
            }).placeAt(this);

            this.attribute = new Select({
                label: i18n.gettext("Attribute"),
                style: "width: 100%"
            }).placeAt(this.container);

            this.values = new CheckedMultiSelect({
                label: i18n.gettext("Values"),
                style: "width: 100%",
                multiple: true
            }).placeAt(this.container);

            domStyle.set(this.values.selectNode, {
                "width": "300px",
                "overflow-x": "scroll"
            });
        },

        postCreate: function () {
            this.inherited(arguments);

            this.attribute.watch("value", lang.hitch(this, function (attr, oldVal, newVal) {
                this.values.removeOption(this.values.getOptions());
                this.attribute.set("disabled", true);

                xhr.get(route.feature_layer.unique_values({
                    id: this.parent.layerId,
                    keyname: newVal
                }), {
                    handleAs: "json"
                }).then(lang.hitch(this, function (data) {
                    var options = array.map(
                        data.unique_values, function (item) {
                            return {
                                value: item,
                                label: item
                            };
                        }
                    );
                    var valueStore = new Memory({data: options});
                    this.values.addOption(valueStore.query(null, {
                        count: settings.filter.limit,
                        sort: [{attribute: "label"}]
                    }));

                    this.attribute.set("disabled", false);
                }));
            }));
        },

        initialize: function (parent) {
            this.parent = parent;
            this.attribute.addOption(array.map(parent._fields, function (field) {
                return {
                    label: field.display_name,
                    value: field.keyname
                };
            }));
        },

        onExecute: function () {
            this.parent._grid.set("query", {
                in: json.stringify({
                    attribute: this.attribute.get("value"),
                    values: this.values.get("value")
                })
            });
        },

        onReset: function () {
            this.values.set("value", []);
            this.values._updateSelection();
            this.parent._grid.set("query", {});
            this.hide();
        }
    });
});
