#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import os
from html2text import html2text, read_file, clean_utf8
from subprocess import Popen, PIPE
from collections import defaultdict
import langid
import unicodedata

magic_numer = "df6fa1abb58549287111ba8d776733e9"


def original_url(html):
    m = re.search(r"<!-- Mirrored from ([^>]+) by HTTrack Website Copier",
                  html)
    if m is None:
        return "unknown_url"
    return m.groups()[0]


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
    if not output.strip():
        # sys.stderr.write("writing debug file.\n")
        # f = open("debug", "w")
        # f.write(header)
        # f.write(text.encode("utf-8"))
        # f.close()

        res = langid.classify(text)
        lang = res[0]
        header = "%s\tlanguage:%s\tbytes:%d\n" % (header.rstrip(),
                                                  lang,
                                                  len(text.encode("utf-8")))
        return header + text
    return output


def mainlang(langsplit_output, expected_langs):
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

    assert stats, stats

    stats = [(b, l) for l, b in stats.items()]
    stats.sort(reverse=True)
    # print stats

    best_idx = 0
    while best_idx < len(stats) - 1 \
            and stats[best_idx][1] not in expected_langs:
        best_idx += 1

    return stats[best_idx][1]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-annotate', help='filelist to annotate',
                        type=argparse.FileType('r'))
    parser.add_argument('-prefix', help='prefix added to make filenames',
                        default="/fs/syn0/pkoehn/crawl/data/site-crawls")
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    # annotate a list of files with their main language
    if args.annotate:
        for line in args.annotate:
            filename = os.path.join(args.prefix,
                                    line.split(":")[0].split("/")[0],
                                    line.split(":")[0])
            html = read_file(filename)
            html = clean_utf8(html)
            text = html2text(html.encode("utf-8"))

            if not text.strip():
                sys.stderr.write("no text found in %s\n" % filename)

            langsplit_output = langsplit(filename, text)
            lang = mainlang(langsplit_output, (args.slang, args.tlang))
            if lang in [args.slang, args.tlang]:
                args.outfile.write("%s\t%s\n" % (line.split(":")[0], lang))
            else:
                sys.stderr.write("Skipping %s : %s\n" % (filename, lang))
        sys.exit()

    correct = 0
    for line in sys.stdin:
        domain, a, b = line.strip().split("\t")

        langs = []
        for s in (a, b):
            filename = os.path.join(args.prefix, domain, s)
            html = read_file(filename)
            html = clean_utf8(html)
            url = original_url(html)
            # print url

            text = html2text(html.encode("utf-8"))

            if not text.strip():
                sys.stderr.write("no text found in %s\n" % filename)

            langsplit_output = langsplit(filename, text)
            lang = mainlang(langsplit_output, (args.slang, args.tlang))

            if lang == "INVALID":
                sys.stderr.write("Error processing: %s\n" % line)
                continue
            if lang not in [args.slang, args.tlang]:
                sys.stderr.write(
                    "Unexpected main language: %s - skipping line '%s'\n"
                    % (lang, line))
                continue
            # args.outfile.write("%s\t%s\n" % (s.strip(), lang))
            langs.append(lang)

        if len(set(langs)) < 2:
            print line, langs
        else:
            correct += 1

    print "Correct: ", correct
