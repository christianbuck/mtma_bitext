#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import os
import chardet
import base64
from html2text import html2text
from subprocess import Popen, PIPE
from collections import defaultdict

magic_numer = "df6fa1abb58549287111ba8d776733e9"


def clean_whitespace(s):
    # remove empty lines
    s = [l.strip() for l in s.split("\n") if l.strip()]
    return "\n".join(re.sub("\s+", " ", l) for l in s)


def read_file(filename, args, encoding):
    full_file_name = os.path.join(args.prefix, filename)
    sys.stderr.write("reading: %s\n" % full_file_name)
    f = open(full_file_name, 'r')
    html = f.read()
    try:
        html = html.decode("utf-8")
    except:
        try:
            html = html.deocde(encoding)
        except:
            encoding = chardet.detect(html)
            try:
                html = html.decode(encoding["encoding"])
            except:
                sys.stderr.write(
                    "Fallback: ignoring errors for file%s\n" % full_file_name)
                return html.decode("utf-8", errors='ignore')
    return html


def langsplit(filename, text):
    cmd = [
        "/home/buck/net/build/mtma_bitext//html_convert/langsplit",
        "--printchunks"]
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    tld = filename.split("/")[0].split(".")[0]
    header = "%s tld:%s uri:%s\n" % (magic_numer, tld, filename)
    proc.stdin.write(header)
    proc.stdin.write(text.encode("utf-8"))
    proc.stdin.write("\n")
    output = proc.communicate()[0]
    return output


def mainlang(langsplit_output):
    stats = defaultdict(int)
    b = None
    l = None
    for line in langsplit_output.split("\n"):
        # df6fa1abb58549287111ba8d776733e9 tld:www
        # uri:www.hettahuskies.com/doghotel/hotel.html language:en offset:0
        # bytes: 3853

        if not line.startswith(magic_numer):
            continue
        for kv in line.split():
            if kv.startswith("bytes:"):
                b = int(kv.split(":", 1)[1])
            elif kv.startswith("language:"):
                l = kv.split(":", 1)[1]
        assert b is not None and l is not None, line
        stats[l] += b

    if not len(stats) > 0:
        sys.stderr.write(langsplit_output + "\n")
        return "INVALID"

    stats = [(b, l) for l, b in stats.items()]
    stats.sort()
    return stats[0][1]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-prefix', help='prefix added to make filenames')
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    for line in sys.stdin:
        vals = line.split()
        # if not len(vals) == 3:
        #     sys.stderr.write("weird line: %s" % "".join(line))
        filename = " ".join(vals[:-2])
        mime, enc = vals[-2:]

        enc = enc.split('=')[-1].strip()
        mime = mime[:-1]  # remove ';'
        filename = filename[:-1]   # remove ':'

        # also converts to unicode string
        html = read_file(filename, args, enc)
        text = html2text(html.encode("utf-8"))
        langsplit_output = langsplit(filename, text)
        lang = mainlang(langsplit_output)

        if lang == "INVALID":
            sys.stderr.write("Error processing: %s\n" % line)
            continue
        if lang not in [args.slang, args.tlang]:
            sys.stderr.write(
                "Unexpected main language: %s - skipping %s\n" % (lang, line))
            continue

        args.outfile.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n"
                           .format(
                               l=lang,
                               mime=mime,
                               enc=enc,
                               name=filename,
                               html=base64.b64encode(html.encode("utf-8")),
                               text=base64.b64encode(text.encode("utf-8"))))
