#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
Reads candidates and writes lett format to be processed by
bitextor pipeline
"""

import sys
import base64
from html2text import html2text
from chardet.universaldetector import UniversalDetector
import subprocess
from threading import Lock


magic_numer = "df6fa1abb58549287111ba8d776733e9"


class ExternalProcessor(object):

    """ wraps an external script and does utf-8 conversions, is thread-safe """

    def __init__(self, cmd):
        self.cmd = cmd
        if self.cmd is not None:
            self.proc = self.popen(cmd)
            self._lock = Lock()

    def popen(self, cmd):
        cmd = cmd.split()
        return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)

    def preprocess_input(self, line):
        return line.replace("\r", "").rstrip()

    def postprocess_output(self, line):
        return line

    def process(self, line):
        # sys.stderr.write("running preprocessor\n")
        line = self.preprocess_input(line)
        u_string = u"%s\n" % line
        u_string = u_string.encode("utf-8")
        result = u_string  # fallback: return input
        # with self._lock:
        # sys.stderr.write("processing %d lines, %d bytes\n"
        #                  % (len(u_string.split("\n")), len(u_string)))
        # sys.stdout.write(u_string)
        self.proc.stdin.write(u_string)
        self.proc.stdin.flush()
        result = self.proc.stdout.readline()
        result = self.postprocess_output(result)
        # sys.stderr.write("read, %d bytes\n"
        #                  % (len(result)))
        return result.decode("utf-8").strip()


class TikaProcessor(ExternalProcessor):

    def __init__(self, tikajar):
        tikacmd = "java -jar %s --inlinexml" % (tikajar)
        super(TikaProcessor, self).__init__(tikacmd)

    def preprocess_input(self, line):
        line = line.strip().replace("\n", " ").replace("\r", "")
        return line

    # def postprocess_output(self, line):
    #     line = line.split("\t")
    #     assert len(line) == 4, line
    #     return line[-1].strip()


class BoiperpipeProcessor(TikaProcessor):

    def __init__(self, tikajar):
        tikacmd = "java -jar %s" % (tikajar)
        super(BoiperpipeProcessor, self).__init__(tikacmd)

    def postprocess_output(self, line):
        line = line.split("\t")
        assert len(line) == 5
        return line[-1].strip()


def process_buffer(buf, d):
    if not buf:
        return
    header = buf[0]
    url = header.split()[1]
    skip = 0
    empty_lines = 0
    while empty_lines < 2:
        skip += 1
        if not buf[skip].strip():
            empty_lines += 1

    html = "".join(buf[skip + 1:])
    try:
        html = html.decode("utf-8")
    except:
        try:
            detector = UniversalDetector()
            for line in buf[skip + 1:]:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            encoding = detector.result
            html = html.decode(encoding["encoding"])
        except:
            html = html.decode("utf-8", errors='ignore')
    html = html.replace(r"\r", "")
    d[url] = (header, html)


def read_file(f, d):
    buf = []
    for line in f:
        line = line
        if line.startswith(magic_numer):
            process_buffer(buf, d)
            buf = [line]
            continue
        buf.append(line)
    process_buffer(buf, d)


def process_dict(d, html_prepro):
    for u, (header, html) in d.iteritems():
        for prepro in html_prepro:
            # sys.stderr.write('.')
            html = prepro.process(html)
        original_url = header.split()[2]
        text = html2text(html.encode("utf-8"))
        # html = base64.b64encode(html.encode("utf-8"))
        yield u, original_url, html, text


def write_lett(sdict, tdict, args):
    mime_type = "text/html"
    encoding = "charset=utf-8"

    html_prepro = []
    if args.tikajar:
        html_prepro.append(TikaProcessor(args.tikajar))
    if args.bpjar:
        html_prepro.append(BoiperpipeProcessor(args.bpjar))

    for l, d in ((args.slang, sdict), (args.tlang, tdict)):
        for url, original_url, html, text in process_dict(d, html_prepro):

            args.outfile.write(
                "{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n"
                .format(
                    l=l,
                    mime=mime_type,
                    enc=encoding,
                    name=original_url,
                    html=base64.b64encode(html.encode("utf-8")),
                    text=base64.b64encode(text.encode("utf-8"))))

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
    parser.add_argument('-tikajar', help='location of jar file for piped tika')
    parser.add_argument(
        '-bpjar', help='location of jar file for piped boilerpipe')
    args = parser.parse_args(sys.argv[1:])

    sdict, tdict = {}, {}
    read_file(args.source, sdict)
    read_file(args.target, tdict)
    write_lett(sdict, tdict, args)
