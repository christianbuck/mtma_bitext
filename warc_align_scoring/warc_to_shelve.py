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
import goslate
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

    # cleaned_sents = [sent for sent in cleaned_sents.split(
    # '\n')]  # if len(sent.split()) == 0 or len(sent.split()) >= 6]
    return cleaned_sents.split('\n')


@retry(goslate.Error, tries=100, delay=1, max_delay=10, jitter=1)
def gtranslate(lines, translate_src_lang):
    logger.info('translate: %s lines', len(lines))
    return gs.translate(lines, 'en', 'fr')


# def print(*vargs, **kvargs): pass


def warc_to_parts(lines, translate_src_lang):
    part_name = 'START'

    warc, http, html = [], [], []
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
                translated_cleaned_html_lines = (
                    list(gtranslate(cleaned_html_lines, translate_src_lang))
                    if translate_src_lang else None)

                yield url, (warc, http, cleaned_html_lines, translated_cleaned_html_lines)

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
    parser.add_argument('-t', '--translate-from', metavar='LANG', dest='SRC_LANG')
    parser.add_argument('SHELVE', help='Output shelve database file')
    parser.add_argument('FILE', nargs='*', help='Input WARC file. (default: stdin)')
    parser.add_argument('-v', '--verbose',  help='Produce verbose message', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parseargs()

    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)

    gs = goslate.Goslate(executor=concurrent.futures.ThreadPoolExecutor(max_workers=120))
    with shelve.open(args.SHELVE) as ted_fr_shelve:
        for url, parts in warc_to_parts(
                fileinput.input(args.FILE),
                args.SRC_LANG):
            ted_fr_shelve[url] = parts
