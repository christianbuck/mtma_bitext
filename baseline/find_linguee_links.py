#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('links', type=argparse.FileType('r'),
                        help='list of links to look for')
    args = parser.parse_args(sys.argv[1:])

    links = ["uri:" + link.strip() for link in args.links]
    links = set(links)

    for line in sys.stdin:
        mn, uri, data = line.split(' ', 2)
        if uri in links:
            print line
