# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..resource import Widget, Resource
from .model import WFSConnection, WFSLayer
from .util import _


class ClientWidget(Widget):
    resource = WFSConnection
    operation = ('create', 'update')
    amdmod = 'ngw-wfsclient/ConnectionWidget'


class LayerWidget(Widget):
    resource = WFSLayer
    operation = ('create', 'update')
    amdmod = 'ngw-wfsclient/LayerWidget'


def setup_pyramid(comp, conf):
    Resource.__psection__.register(
        key='wfsclient_connection', priority=50,
        title=_("WFS capabilities"),
        is_applicable=lambda obj: (
            obj.cls == 'wfsclient_connection'
            and obj.capcache()),
        template='nextgisweb:wfsclient/template/section_connection.mako')
