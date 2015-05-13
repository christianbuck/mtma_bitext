#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import logging
import fileinput
import htmllaundry
import tidylib
import re
import shelve
from bs4 import BeautifulSoup
import argparse
import concurrent.futures
import shelve
from retry import retry
import os.path


def html_cleaner(html):
    soup = BeautifulSoup('\n'.join(html))
    [s.extract() for s in soup('script')]  # remove 'script', 'style', 'option' tags
    [s.extract() for s in soup('style')]
    [s.extract() for s in soup('option')]

    cleaned_sents = htmllaundry.strip_markup(str(soup))  # leave only text

    # remove continuous empty lines
    cleaned_sents = re.sub(r'\n\s*\n+', '\n\n', cleaned_sents).strip()
    cleaned_sents = re.sub(r'\s+', ' ', cleaned_sents, re.M).strip()  # remove continuous spaces

    return cleaned_sents

def warc_to_parts(lines):
    part_name = 'START'

    warc, http, html = [], [], []
    cnt = 0

    for line in lines:
        line = line.strip()

        if part_name == 'START':
            if line == '':
                continue
            else:
                part_name = 'WARC'

        if part_name == 'WARC':
            if line.startswith('WARC-Target-URI: '):
                url = line[len('WARC-Target-URI: '):]
            if line == '':
                part_name = 'HTTP'
                continue
            warc.append(line)

        elif part_name == 'HTTP':
            if line == '':
                part_name = 'HTML'
                continue
            http.append(line)

        elif part_name == 'HTML':
            html.append(line)
            if line == '</html>':
                part_name = 'START'

                cleaned_html_lines = html_cleaner(html)
                cnt += 1

                yield url, (warc, http, cleaned_html_lines)
                warc, http, html = [], [], []


def get_logger(lvl):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.setLevel(lvl)
    ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        ' \033[1;32m*\033[m %(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%m/%d/%Y %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('FILE', nargs='*', help='Input WARC file. (default: stdin)')
    parser.add_argument('-v', '--verbose',  help='Produce verbose message', action='store_true')
    return parser.parse_args()

if __name__ == '__main__':
    args = parseargs()
    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)
    
    cleaned_file = open(args.FILE[0] + "_cleanedHTML", 'w+')
    url_file = open(args.FILE[0] + "_url", 'w+')

    for url, parts in warc_to_parts(fileinput.input(args.FILE)):
        url_file.write(url + '\n')
        cleaned_file.write("NEW_ENTRY" + '\n')
        cleaned_file.write(parts[2] + '\n')
        