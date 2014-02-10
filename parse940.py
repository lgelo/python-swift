#!/usr/bin/env python

from swift import SwiftReader
from swift.TabaSK import TabaParser940

if __name__ == '__main__':
    import os, glob
    pattern = "download/*.STA"

    parser = SwiftReader(TabaParser940)
    for filename in glob.glob(pattern):
        print "Parsing %s ..." % filename
        statements = parser.parse_file(filename)
        for st in statements:
            print "Statement:\n", st.to_json()
