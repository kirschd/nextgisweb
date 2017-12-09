# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from datetime import datetime
from collections import OrderedDict

from lxml import etree
from owslib.wfs import WebFeatureService
from owslib.feature.common import WFSCapabilitiesReader
from zope.interface import implements

from .. import db
from ..models import declarative_base
from ..layer import SpatialLayerMixin
from ..feature_layer import (
    GEOM_TYPE,
    LayerField,
    LayerFieldsMixin,
    IFeatureLayer)

from ..resource import (
    Resource,
    ResourceGroup,
    DataScope,
    ConnectionScope,
    Serializer,
    SerializedProperty as SP)

from .util import _

Base = declarative_base()

WFS_VERSIONS = ('1.1.0',)


class Connection(Base, Resource):
    identity = 'wfsclient_connection'
    cls_display_name = _("WFS connection")

    __scope__ = ConnectionScope

    url = db.Column(db.Unicode, nullable=False)
    version = db.Column(db.Enum(*WFS_VERSIONS), nullable=False)
    username = db.Column(db.Unicode)
    password = db.Column(db.Unicode)

    capcache_xml = db.deferred(db.Column(db.Unicode))
    capcache_json = db.deferred(db.Column(db.Unicode))
    capcache_tstamp = db.Column(db.DateTime)

    @classmethod
    def check_parent(cls, parent):
        return isinstance(parent, ResourceGroup)

    def capcache(self):
        return self.capcache_json is not None \
            and self.capcache_xml is not None \
            and self.capcache_tstamp is not None

    def capcache_query(self):
        self.capcache_tstamp = datetime.utcnow()
        reader = WFSCapabilitiesReader(self.version,
                                       username=self.username,
                                       password=self.password)
        self.capcache_xml = etree.tostring(reader.read(self.url))

        service = WebFeatureService(
            url=self.url, version=self.version,
            username=self.username,
            password=self.password,
            xml=str(self.capcache_xml))

        layers = []
        for lid, layer in service.contents.iteritems():
            layers.append(OrderedDict((
                ('id', lid),
                ('title', layer.title),
                ('schema', service.get_schema(lid))
            )))

        data = OrderedDict((
            ('formats', service.getOperationByName('GetFeature').formatOptions),
            ('layers', layers),
        ))

        self.capcache_json = json.dumps(data, ensure_ascii=False)

    def capcache_clear(self):
        self.capcache_xml = None
        self.capcache_json = None
        self.capcache_tstamp = None

    @property
    def capcache_dict(self):
        if not self.capcache():
            return None

        return json.loads(self.capcache_json)


class _capcache_attr(SP):

    def getter(self, srlzr):
        return srlzr.obj.capcache_dict \
            if srlzr.obj.capcache() else None

    def setter(self, srlzr, value):
        if value == 'query':
            srlzr.obj.capcache_query()
        elif value == 'clear':
            srlzr.obj.capcache_clear()
        else:
            raise ValidationError(_('Invalid capcache value!'))


class ConnectionSerializer(Serializer):
    identity = Connection.identity
    resclass = Connection

    _defaults = dict(read=ConnectionScope.read,
                     write=ConnectionScope.write)

    url = SP(**_defaults)
    version = SP(**_defaults)
    username = SP(**_defaults)
    password = SP(**_defaults)

    capcache = _capcache_attr(
        read=ConnectionScope.connect,
        write=ConnectionScope.connect)
