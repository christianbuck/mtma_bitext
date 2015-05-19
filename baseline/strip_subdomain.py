#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import tldextract


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-domainonly', action='store_true',
                        help='remove tld as well')
    args = parser.parse_args(sys.argv[1:])

    for line in sys.stdin:
        host, data = line.split(" ", 1)
        parts = tldextract.extract(host)
        if parts.domain == "":
            host = parts.suffix
        elif parts.suffix == "" or args.domainonly:
            host = parts.domain
        else:
            host = "%s.%s" % (parts.domain, parts.suffix)
        sys.stdout.write("%s %s" % (host.encode("idna"), data))
