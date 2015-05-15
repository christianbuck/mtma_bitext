#!/usr/bin/env python
# -*- coding: utf-8 -*-

import langid
import sys

for line in sys.stdin:
    lang, confidence = langid.classify(line.strip())
    if confidence < 0.5:
        lang = 'un'
    sys.stdout.write("%s %s" % (lang, line))
