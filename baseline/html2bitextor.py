#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
Reads candidates and writes lett format to be processed by

"""

import sys
import base64
from html2text import html2text
from chardet.universaldetector import UniversalDetector

magic_numer = "df6fa1abb58549287111ba8d776733e9"


def process_buffer(buf):
    html = "".join(buf)
    try:
        html = html.decode("utf-8")
    except:
        try:
            detector = UniversalDetector()
            for line in buf:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            encoding = detector.result
            html = html.decode(encoding["encoding"], errors='ignore')
        except:
            html = html.decode("utf-8", errors='ignore')
    return html


def read_file(f):
    buf = ["source_file"]
    for line in f:
        buf.append(line)
    return process_buffer(buf)


def process_dict(d):
    for u, (header, html) in d.iteritems():
        original_url = header.split()[2]
        text = html2text(html.encode("utf-8"))
        # html = base64.b64encode(html.encode("utf-8"))
        yield u, original_url, html, text


def write_lett(s, t, slang, tlang, f):
    mime_type = "text/html"
    encoding = "charset=utf-8"

    stext = html2text(s.encode("utf-8"))
    f.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n".format(
        l=slang,
        mime=mime_type,
        enc=encoding,
        name="source_file",
        html=base64.b64encode(s.encode("utf-8")),
        text=base64.b64encode(stext.encode("utf-8"))))

    ttext = html2text(t.encode("utf-8"))
    f.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n".format(
        l=tlang,
        mime=mime_type,
        enc=encoding,
        name="source_file",
        html=base64.b64encode(t.encode("utf-8")),
        text=base64.b64encode(ttext.encode("utf-8"))))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=argparse.FileType('r'),
                        help='source corpus')
    parser.add_argument('target', type=argparse.FileType('r'),
                        help='target corpus')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    s = read_file(args.source)
    t = read_file(args.target)
    write_lett(s, t, args.slang, args.tlang, args.outfile)
