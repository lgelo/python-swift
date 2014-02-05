#!/usr/bin/env python

from swift import SwiftReader
from swift.TabaSK import TabaParser942

if __name__ == '__main__':
    import os, glob
    pattern = "download/*.VML"

    parser = SwiftReader(TabaParser942)
    for filename in glob.glob(pattern):
        print "Parsing %s ..." % filename
        statements = parser.parse_file(filename)
