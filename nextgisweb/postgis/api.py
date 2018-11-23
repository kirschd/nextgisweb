# -*- coding: utf-8 -*-
import json

from sqlalchemy import inspect
from pyramid.response import Response

from .model import PostgisConnection
from ..resource import resource_factory


def inspect_connection(request):
    connection = request.context
    inspector = inspect(connection.get_engine())
    
    result = []
    for schema_name in inspector.get_schema_names():
        if schema_name != 'information_schema':
            result.append(dict(
                schema=schema_name,
                views=inspector.get_view_names(schema=schema_name),
                tables=inspector.get_table_names(schema=schema_name)))

    return Response(json.dumps(result), content_type=b'application/json')


def setup_pyramid(comp, config):
    config.add_route(
        'postgis.connection.inspect', '/api/resource/{id}/inspect/',
        factory=resource_factory) \
        .add_view(inspect_connection, context=PostgisConnection, request_method='GET')
