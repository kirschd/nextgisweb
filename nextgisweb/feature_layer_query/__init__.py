# -*- coding: utf-8 -*-
from ..component import Component, require
from .model import Base, QueryLayer

__all__ = ['QueryLayer', ]


class QueryLayerComponent(Component):
    identity = 'feature_layer_query'
    metadata = Base.metadata

    def initialize(self):
        super(QueryLayerComponent, self).initialize()

    @require('feature_layer')
    def setup_pyramid(self, config):
        from . import view  # NOQA
