# -*- coding: utf-8 -*-
from ..resource import Widget
from .model import QueryLayer


class QueryLayerWidget(Widget):
    resource = QueryLayer
    operation = ('create', 'update')
    amdmod = 'ngw-feature-layer-query/LayerWidget'
