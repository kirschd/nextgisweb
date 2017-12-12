# -*- coding: utf-8 -*-

from rest_query import BaseParamsParser, ParserException

OPMAP = {'=': 'eq', '!=': 'ne',
         '>': 'gt', '>=': 'ge',
         '<': 'lt', '<=': 'le'}


class ParamsParser(BaseParamsParser):
    exclude_where = []


class QueryMixin(object):

    def filter_by_query(self, query=None):
        if query is not None:
            parser = ParamsParser(params_args=query)

        filters = []
        where = parser.parse_where()
        for clause in where:
            if clause['op'] in OPMAP:
                filters.append(
                    (clause['field'], OPMAP[clause['op']], clause['value']))
            elif clause['op'] == 'between':
                filters.extend((
                    (clause['field'], OPMAP['>='], clause['value'][0]),
                    (clause['field'], OPMAP['<='], clause['value'][1])))

        self._filter = self._filter if self._filter is not None else []
        self._filter.extend(filters)
