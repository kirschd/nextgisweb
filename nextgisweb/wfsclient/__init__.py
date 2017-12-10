# -*- coding: utf-8 -*-
from ..component import Component
from .model import (
    Base,
    WFSConnection,
    WFSLayer,
    WFS_VERSIONS)

__all__ = ['WFSConnection', 'WFSLayer']


class WFSClientComponent(Component):
    identity = 'wfsclient'
    metadata = Base.metadata

    def initialize(self):
        super(WFSClientComponent, self).initialize()

    def setup_pyramid(self, config):
        from . import view
        view.setup_pyramid(self, config)

    def client_settings(self, request):
        return dict(wfs_versions=WFS_VERSIONS)
