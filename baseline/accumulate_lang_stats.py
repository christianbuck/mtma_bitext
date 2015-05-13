#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Read raw text dumps from http://data.statmt.org/ngrams/raw/
and prints url and number of bytes
"""

import sys
from collections import defaultdict

buf = defaultdict(int)
domain = None

for line in sys.stdin:
    d, lang, n = line.split()
    n = int(n)
    if domain != d:
        for l in buf:
            sys.stdout.write("%s %s %d\n" % (domain, l, buf[l]))
        buf = defaultdict(int)
    buf[lang] += n

for l in buf:
    sys.stdout.write("%s %s %d\n" % (domain, l, buf[l]))
