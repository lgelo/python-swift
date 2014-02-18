#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decimal import Decimal
from datetime import date
from json import JSONEncoder
from itertools import chain

class JSONObject(object):

    _json_ignore = ()

    def _attrs(self):
        return list(set(chain(*[getattr(cls, '__slots__', []) for cls in type(self).__mro__])))

    def to_json(self):
        return dict((k, getattr(self,k,'')) \
            for k in self._attrs() if not (k.startswith('_') or k in self._json_ignore))


class MTJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, JSONObject):
            return obj.to_json()

        return JSONEncoder.default(self, obj)

class SwiftReader(object):

    def __init__(self, parser):
        self._parser_class = parser
        self._parser = self._parser_class()

    def parse_file(self, filename):
        with open(filename) as file:
            return self.parse(file.read().splitlines())

    def parse(self, lines):
        return self._parser.parse(lines)
