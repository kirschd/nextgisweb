# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from pyramid.response import Response

from ..resource import DataScope, resource_factory
from .interface import IBboxLayer


def extent(resource, request):
    """
    ---
    get:
        summary: Get extent of the layer in geographic coordinates.
        description: This method doesn't work for PostGIS layers.
        parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
          description: Resource ID
        produces:
        - application/json
        responses:
          200:
            description: success
            schema:
              type: object
              properties:
                extent:
                  type: object
                  properties:
                    minLat:
                      type: number
                    maxLon:
                      type: number
                    minLon:
                      type: number
                    maxLat:
                      type: number
    """
    request.resource_permission(DataScope.read)

    extent = resource.extent

    return Response(
        json.dumps(dict(extent=extent)),
        content_type=b'application/json')


def setup_pyramid(comp, config):
    config.add_route(
        'layer.extent', '/api/resource/{id}/extent',
        factory=resource_factory) \
        .add_view(extent, context=IBboxLayer, request_method='GET')
