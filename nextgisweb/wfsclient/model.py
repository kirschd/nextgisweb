# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import uuid

from datetime import datetime
from collections import OrderedDict

from lxml import etree
from osgeo import gdal, ogr
from owslib import fes
from owslib.wfs import WebFeatureService
from owslib.feature.common import WFSCapabilitiesReader
from zope.interface import implements

from .. import db
from ..env import env
from ..models import declarative_base
from ..geometry import geom_from_wkb, box
from ..layer import SpatialLayerMixin
from ..feature_layer import (
    FIELD_TYPE,
    GEOM_TYPE,
    GEOM_TYPE_DISPLAY,
    IFeatureQuery,
    IFeatureQueryFilterBy,
    IFeatureQueryIntersects,
    Feature,
    FeatureSet,
    LayerField,
    LayerFieldsMixin,
    IFeatureLayer)

from ..resource import (
    Resource,
    ResourceGroup,
    DataScope,
    DataStructureScope,
    ConnectionScope,
    ValidationError,
    ResourceError,
    Serializer,
    SerializedProperty as SP,
    SerializedRelationship as SR,
    SerializedResourceRelationship as SRR)

from .util import _

Base = declarative_base()

WFS_VERSIONS = ('1.1.0',)


class WFSConnection(Base, Resource):
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

    def get_service(self):
        service = WebFeatureService(
            url=self.url, version=self.version,
            username=self.username,
            password=self.password,
            xml=str(self.capcache_xml))

        return service

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

        service = self.get_service()

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
            raise ValidationError(_("Invalid capcache value!"))


class WFSConnectionSerializer(Serializer):
    identity = WFSConnection.identity
    resclass = WFSConnection

    _defaults = dict(read=ConnectionScope.read,
                     write=ConnectionScope.write)

    url = SP(**_defaults)
    version = SP(**_defaults)
    username = SP(**_defaults)
    password = SP(**_defaults)

    capcache = _capcache_attr(
        read=ConnectionScope.connect,
        write=ConnectionScope.connect)


class WFSLayerField(Base, LayerField):
    identity = 'wfsclient_layer'

    __tablename__ = LayerField.__tablename__ + '_' + identity
    __mapper_args__ = dict(polymorphic_identity=identity)

    id = db.Column(db.ForeignKey(LayerField.id), primary_key=True)
    column_name = db.Column(db.Unicode, nullable=False)


class WFSLayer(Base, Resource, SpatialLayerMixin, LayerFieldsMixin):
    identity = 'wfsclient_layer'
    cls_display_name = _("WFS layer")

    __scope__ = DataScope

    implements(IFeatureLayer, )

    connection_id = db.Column(db.ForeignKey(Resource.id), nullable=False)
    typename = db.Column(db.Unicode, nullable=False)
    geometry_column = db.Column(db.Unicode, nullable=False)
    geometry_type = db.Column(db.Enum(*GEOM_TYPE.enum), nullable=False)

    __field_class__ = WFSLayerField

    connection = db.relationship(
        Resource,
        foreign_keys=connection_id,
        cascade=False, cascade_backrefs=False)

    @classmethod
    def check_parent(cls, parent):
        return isinstance(parent, ResourceGroup)

    def setup(self):
        fdata = {}
        for f in self.fields:
            fdata[f.keyname] = {
                'display_name': f.display_name,
                'grid_visibility': f.grid_visibility
            }

        self.fields = []

        self.feature_label_field = None

        capcache = self.connection.capcache_json
        if capcache is None:
            raise ValidationError(_("Capcache is empty."))

        capcache = json.loads(capcache)
        for layer in capcache.get('layers'):
            lid = layer.get('id')
            if lid == self.typename:
                schema = layer.get('schema')
                properties = schema.get('properties')
                geomtype = schema.get('geometry').upper()

                if geomtype in GEOM_TYPE.enum:
                    self.geometry_type = geomtype
                elif geomtype == '3D POLYGON':
                    self.geometry_type = 'POLYGON'
                elif geomtype == '3D MULTIPOLYGON':
                    self.geometry_type = 'MULTIPOLYGON'
                else:
                    raise ValidationError(_(
                        "Geometry type %s is not supported." % geomtype))

                geomcolumn = schema.get('geometry_column')
                self.geometry_column = geomcolumn

                for column_name, column_type in properties.iteritems():
                    if column_name in ('id', 'geom'):
                        pass
                    else:
                        datatype = None
                        if column_type == 'int':
                            datatype = FIELD_TYPE.INTEGER
                        elif column_type == 'double':
                            datatype = FIELD_TYPE.REAL
                        elif column_type == 'string':
                            datatype = FIELD_TYPE.STRING

                    if datatype is not None:
                        fopts = {'display_name': column_name}
                        fopts.update(fdata.get(column_name, {}))
                        self.fields.append(WFSLayerField(
                            keyname=column_name,
                            datatype=datatype,
                            column_name=column_name,
                            **fopts))

    def get_info(self):
        return super(WFSLayer, self).get_info() + (
            (_("Geometry type"),
             dict(zip(GEOM_TYPE.enum,
                      GEOM_TYPE_DISPLAY))[self.geometry_type]),
        )

    # IFeatureLayer

    @property
    def feature_query(self):

        class BoundFeatureQuery(FeatureQueryBase):
            layer = self

        return BoundFeatureQuery

    def field_by_keyname(self, keyname):
        for f in self.fields:
            if f.keyname == keyname:
                return f

        raise KeyError(_("Field '%s' not found!") % keyname)

DataScope.read.require(
    ConnectionScope.connect,
    attr='connection', cls=WFSLayer)


class _fields_action(SP):

    def setter(self, srlzr, value):
        if value == 'update':
            srlzr.obj.setup()
        elif value != 'keep':
            raise ResourceError()


class WFSLayerSerializer(Serializer):
    identity = WFSLayer.identity
    resclass = WFSLayer

    __defaults = dict(read=DataStructureScope.read,
                      write=DataStructureScope.write)

    connection = SRR(**__defaults)

    typename = SP(**__defaults)
    srs = SR(**__defaults)

    fields = _fields_action(write=DataStructureScope.write)


class FeatureQueryBase(object):
    implements(
        IFeatureQuery,
        IFeatureQueryFilterBy,
        IFeatureQueryIntersects,)

    def __init__(self):
        self._srs = None
        self._geom = None
        self._box = None

        self._fields = None
        self._limit = None
        self._offset = None

        self._filter_by = None
        self._intersects = None

    def srs(self, srs):
        self._srs = srs

    def geom(self):
        self._geom = True

    def box(self):
        self._box = True

    def fields(self, *args):
        self._fields = args

    def limit(self, limit, offset=0):
        self._limit = limit
        self._offset = offset

    def filter_by(self, **kwargs):
        self._filter_by = kwargs

    def intersects(self, geom):
        self._intersects = geom

    def __call__(self):
        srsname = 'EPSG:%d' % (
            self.layer.srs_id if self._srs is None else self._srs.id)

        maxfeatures = None
        startindex = None
        if self._limit:
            maxfeatures = self._limit
            startindex = self._offset

        propertynames = []
        for idx, fld in enumerate(self.layer.fields):
            if not self._fields or fld.keyname in self._fields:
                propertynames.append(fld.column_name)

        if self._box:
            self._geom = True

        if self._geom:
            propertynames.append(self.layer.geometry_column)

        featureid = None
        if self._filter_by:
            for k, v in self._filter_by.iteritems():
                if k == 'id':
                    featureid = ['%s.%s' % (
                        self.layer.typename.split(':')[-1], v)]

        intersects = None
        if self._intersects:
            intersects = self._intersects.bounds + (srsname, )

        class QueryFeatureSet(FeatureSet):
            layer = self.layer

            _geom = self._geom
            _box = self._box
            _fields = self._fields
            _limit = self._limit
            _offset = self._offset

            @staticmethod
            def get_layer(response):
                fname = uuid.uuid4().hex
                gdal.FileFromMemBuffer('/vsimem/%s' % (fname, ),
                                       response.getvalue())
                ds = ogr.Open('/vsimem/%s' % (fname, ))
                return (ds.GetLayer(0), ds)

            def __iter__(self):
                service = self.layer.connection.get_service()
                response = service.getfeature(
                    typename=self.layer.typename,
                    featureid=featureid,
                    propertyname=','.join(propertynames),
                    maxfeatures=maxfeatures,
                    startindex=startindex,
                    srsname=srsname,
                    bbox=intersects
                )

                ogrlayer, _ = self.get_layer(response)
                ogrldefn = ogrlayer.GetLayerDefn()
                for f in ogrlayer:

                    geom = None
                    if self._geom:
                        geomref = f.GetGeometryRef()
                        gtype = geomref.GetGeometryType()

                        if gtype == ogr.wkbSurface:
                            geomref = ogr.ForceToPolygon(geomref)
                        elif gtype == ogr.wkbMultiSurface:
                            geomref = ogr.ForceToMultiPolygon(geomref)

                        geom = geom_from_wkb(geomref.ExportToWkb())

                    envelope = None
                    if self._box:
                        ogrbox = f.GetGeometryRef().GetEnvelope()
                        envelope = box(ogrbox[0], ogrbox[2],
                                       ogrbox[1], ogrbox[3])

                    yield Feature(
                        layer=self.layer, id=f.GetFID(),
                        geom=geom, box=envelope,
                        fields=[
                            (ogrldefn.GetFieldDefn(i).GetName(), f.GetField(i))
                            for i in range(ogrldefn.GetFieldCount())
                        ]
                    )

            @property
            def total_count(self):
                service = self.layer.connection.get_service()
                response = service.getfeature(
                    typename=self.layer.typename,
                    propertyname='(,)'
                )
                ogrlayer, _ = self.get_layer(response)
                return ogrlayer.GetFeatureCount()

        return QueryFeatureSet()
