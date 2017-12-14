# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import json

from zope.interface import implements

from .. import db
from ..models import declarative_base
from ..resource import (
    Resource,
    ResourceGroup,
    Serializer,
    SerializedProperty as SP,
    SerializedResourceRelationship as SRR,
    DataScope,
    DataStructureScope)
from ..resource.exception import ValidationError
from ..feature_layer import (
    ParamsParser,
    ParserException,
    LayerField,
    LayerFieldsMixin,
    IFeatureLayer,
    IWritableFeatureLayer)

from .util import _

Base = declarative_base()


class QueryLayerField(Base, LayerField):
    identity = 'query_layer'

    __tablename__ = LayerField.__tablename__ + '_' + identity
    __mapper_args__ = dict(polymorphic_identity=identity)

    id = db.Column(db.ForeignKey(LayerField.id), primary_key=True)


class QueryLayer(Base, Resource, LayerFieldsMixin):
    identity = 'query_layer'
    cls_display_name = _("Query layer")

    __scope__ = DataScope

    implements(IFeatureLayer, IWritableFeatureLayer)

    source_id = db.Column(db.ForeignKey(Resource.id), nullable=False)
    query = db.Column(db.Unicode, nullable=False)

    __field_class__ = QueryLayerField

    source = db.relationship(
        Resource,
        foreign_keys=source_id,
        cascade=False, cascade_backrefs=False)

    def setup(self):
        fdata = {}
        for f in self.fields:
            fdata[f.keyname] = {
                'display_name': f.display_name,
                'grid_visibility': f.grid_visibility
            }

        self.fields = []
        self.feature_label_field = None

        for field in self.source.fields:
            fopts = {'display_name': field.display_name}
            fopts.update(fdata.get(field.keyname, {}))
            self.fields.append(QueryLayerField(
                keyname=field.keyname,
                datatype=field.datatype,
                **fopts))

    @property
    def geometry_type(self):
        return self.source.geometry_type

    @property
    def srs(self):
        return self.source.srs

    @property
    def srs_id(self):
        return self.source.srs_id

    @classmethod
    def check_parent(cls, parent):
        return isinstance(parent, ResourceGroup)

    # IFeatureLayer
    def feature_query(self):
        query = self.source.feature_query()
        query.filter_by_query(json.loads(self.query))
        return query

    def field_by_keyname(self, keyname):
        for f in self.fields:
            if f.keyname == keyname:
                return f

        raise KeyError("Field %r not found!" % keyname)

    def get_info(self):
        s = super(QueryLayer, self)
        return (s.get_info() if hasattr(s, 'get_info') else ()) + (
            (_("Source"), self.source.id),
        )

    # IWritableFeatureLayer
    def feature_put(self, feature):
        self.source.feature_put(feature)

    def feature_create(self, feature):
        self.source.feature_create(feature)

    def feature_delete(self, feature_id):
        self.source.feature_delete(feature_id)

    def feature_delete_all(self):
        self.source.feature_delete_all()


class _query_attr(SP):

    def setter(self, srlzr, value):
        try:
            parser = ParamsParser(params_args=json.loads(value))
            parser.parse_where()

        except ValueError as e:
            raise ValidationError(_("Query should be a valid JSON object."))

        except ParserException as e:
            raise ValidationError(_("Query has an invalid syntax."))

        SP.setter(self, srlzr, value)


class _fields_attr(SP):

    def setter(self, srlzr, value):
        srlzr.obj.setup()


class QueryLayerSerializer(Serializer):
    identity = QueryLayer.identity
    resclass = QueryLayer

    __defaults = dict(read=DataStructureScope.read,
                      write=DataStructureScope.write)

    source = SRR(**__defaults)
    query = _query_attr(**__defaults)
    fields = _fields_attr(read=None, write=DataStructureScope.write)
