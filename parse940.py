#!/usr/bin/env python

import json
from swift import SwiftReader, MTJSONEncoder
from swift.TabaSK import TabaParser940

if __name__ == '__main__':
    import os, glob
    pattern = "download/*.STA"

    for filename in glob.glob(pattern):
        print "Parsing %s ..." % filename
        parser = SwiftReader(TabaParser940)
        statements = parser.parse_file(filename)
        print json.dumps(statements, cls=MTJSONEncoder, sort_keys = True, indent = 2)
