#!/usr/bin/env python
# -*- coding: utf-8 -*-

class SwiftReader(object):

    def __init__(self, parser):
        self._parser_class = parser
        self._parser = self._parser_class()

    def parse_file(self, filename):
        with open(filename) as file:
            return self.parse(file.read().splitlines())

    def parse(self, lines):
        return self._parser.parse(lines)
