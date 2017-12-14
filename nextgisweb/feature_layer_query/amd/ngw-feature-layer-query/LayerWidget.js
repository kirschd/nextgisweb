/* globals define */
define([
    "dojo/_base/declare",
    "dijit/_WidgetBase",
    "dijit/_TemplatedMixin",
    "dijit/_WidgetsInTemplateMixin",
    "ngw-pyramid/i18n!feature_layer_query",
    "ngw-pyramid/hbs-i18n",
    "ngw-resource/serialize",
    "dojo/text!./template/LayerWidget.hbs",
    "xstyle/css!./resource/LayerWidget.css",
    "dijit/form/TextBox",
    "dojox/layout/TableContainer",
    "ngw-resource/ResourceBox",
    "ngw-pyramid/form/CodeMirror"
], function (
    declare,
    _WidgetBase,
    _TemplatedMixin,
    _WidgetsInTemplateMixin,
    i18n,
    hbsI18n,
    serialize,
    template
) {
    return declare([_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, serialize.Mixin], {
        title: i18n.gettext("Query layer"),
        templateString: hbsI18n(template, i18n),
        prefix: "query_layer"
    });
});
