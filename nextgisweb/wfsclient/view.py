# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..resource import Widget, Resource
from .model import Connection  # , Layer
from .util import _


class ClientWidget(Widget):
    resource = Connection
    operation = ('create', 'update')
    amdmod = 'ngw-wfsclient/ConnectionWidget'


def setup_pyramid(comp, conf):
    Resource.__psection__.register(
        key='wfsclient_connection', priority=50,
        title=_("WFS capabilities"),
        is_applicable=lambda obj: (
            obj.cls == 'wfsclient_connection'
            and obj.capcache()),
        template='nextgisweb:wfsclient/template/section_connection.mako')
