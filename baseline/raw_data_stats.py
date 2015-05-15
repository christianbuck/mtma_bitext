#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Read raw text dumps from http://data.statmt.org/ngrams/raw/
and prints url and number of bytes
"""

import sys
from urlparse import urlparse

magic_numer = "df6fa1abb58549287111ba8d776733e9"


def process_buffer(buf, langcode):
    if not buf:
        return
    url = buf[0]
    nbytes = len("".join(buf[1:])) - (len(buf) + 1)
    sys.stdout.write("%s\t%s\t%d\n" % (url, langcode, nbytes))


def get_domain(url):
    return urlparse(url).netloc

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('langcode', help='language code, e.g. en')
    args = parser.parse_args(sys.argv[1:])

    buf = []
    for line in sys.stdin:
        if line.startswith(magic_numer):
            url = line.split()[2].rstrip()
            url = get_domain(url)
            if buf and buf[0] == url:
                continue
            process_buffer(buf, args.langcode)
            buf = [url]
            continue
        buf.append(line)
    process_buffer(buf, args.langcode)


