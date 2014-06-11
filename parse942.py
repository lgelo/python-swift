#!/usr/bin/env python

import json
from swift import SwiftReader, MTJSONEncoder
from swift.TabaSK import TabaParser942

if __name__ == '__main__':
    import os, glob
    pattern = "download/*.VML"

    for filename in glob.glob(pattern):
        print "Parsing %s ..." % filename
        parser = SwiftReader(TabaParser942)
        statements = parser.parse_file(filename)
        print json.dumps(statements, cls=MTJSONEncoder, sort_keys = True, indent = 2)
