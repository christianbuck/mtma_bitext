#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import logging
import fileinput
# import htmllaundry
from tidylib import tidy_document
import re
from bs4 import BeautifulSoup
import argparse
import goslate
import concurrent.futures
import shelve
from retry import retry
import os.path


from itertools import takewhile


def process_buffer(buf):
    line_iter = iter(buf)
    header = next(line_iter).strip().split('\t')[1:]
    warc_header = '\n'.join(takewhile(lambda x: x.strip() != '', line_iter))
    http_header = '\n'.join(takewhile(lambda x: x.strip() != '', line_iter))
    html_content = '\n'.join(line_iter)
    return header, warc_header, http_header, html_content


MAGIC_NUMER = "df6fa1abb58549287111ba8d776733e9"


def read_warc_file(f):
    buf = []
    for line in f:
        if line.startswith(MAGIC_NUMER) and buf:
            yield process_buffer(buf)
            buf = []
        buf.append(line)
    yield process_buffer(buf)


def get_logger(lvl):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.setLevel(lvl)
    logger.handlers = []
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

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-g', '--google-translate',
                       nargs=2, metavar=('SRC_LANG', 'TGT_LANG'),
                       help='Google Translate', )
    group.add_argument('-d', '--dictionary-translate',
                       nargs=2, metavar=('SRC_LANG', 'DICTIONARY_FILE'),
                       help='Dictionary translate', )

    parser.add_argument('SHELVE', help='Output shelve database file')
    parser.add_argument('FILE', nargs='*',
                        help='Input WARC file. (default: stdin)')

    parser.add_argument('-v', '--verbose',
                        help='Produce verbose message', action='store_true')
    parser.add_argument('-n', '--number',
                        help='Number of pages to process', type=int, dest='NUM')

    return parser.parse_args()


from nltk.tokenize import sent_tokenize, word_tokenize


def html_sent_word_tokenize(html_lines):
    for line in html_lines:
        line = line.strip()
        if line.startswith('<'):
            yield line
        else:
            for sent in sent_tokenize(line):
                yield ' '.join(word_tokenize(sent))


def html_clean(html):
    import lxml.html.clean
    import lxml.html
    import lxml.etree

    html, errors = tidy_document(html,
                                 # Tidy options: http://tidy.sourceforge.net/docs/quickref.html
                                 options={'bare': 1, 'clean': 1, 'output-xhtml': 1,
                                          'drop-font-tags': 1, 'drop-proprietary-attributes': 1,
                                          'hide-comments': 1,
                                          'char-encoding': 'utf8', 'input-encoding': 'utf8', 'output-encoding': 'utf8'})
    cleaner = lxml.html.clean.Cleaner(
        kill_tags=frozenset(['script', 'style', 'option']),
        remove_tags=frozenset(['a', 'strong', 'em']),
        safe_attrs_only=True, safe_attrs=frozenset())
    html = cleaner.clean_html(html)

    # html = lxml.etree.tostring(lxml.html.fromstring(html), pretty_print=True).decode('utf8')

    # html = html.encode('utf-8', errors='strict')
    soup = BeautifulSoup(html)
    # [s.extract() for s in soup('script')]  # remove 'script', 'style', 'option' tags
    # [s.extract() for s in soup('style')]
    # [s.extract() for s in soup('option')]
    html = soup.prettify()

    # html = htmllaundry.strip_markup(html)  # leave only text

    # remove continuous empty lines
    html = re.sub(r'\n\s*\n+', '\n\n', html).strip()
    html = re.sub(r'[ \t]+', ' ', html, re.M).strip()  # remove continuous spaces

    # cleaned_html = [sent for sent in cleaned_html.split(
    # '\n')]  # if len(sent.split()) == 0 or len(sent.split()) >= 6]
    html_lines = html.split('\n')
    # return html_lines
    return list(html_sent_word_tokenize(html_lines))

import cld2


@retry(goslate.Error, tries=100, delay=1, max_delay=10, jitter=1)
def google_translator(line, tgt_lang, src_lang):
    return ' '.join(word_tokenize(gs.translate(line, tgt_lang, src_lang)))


def dictionary_translator(line, dictionary):
    return ' '.join(dictionary.get(word.lower(), word) for word in line.split())




def translate_line_or_not(line, src_lang, translator):  # -> (translation, tag)
    if (not line or
            line.startswith('<') and line.endswith('>')):
        return line, ''

    try:
        isReliable, _, lang_details = cld2.detect(line)
    except ValueError:
        return line, 'ValueError'

    if not isReliable or lang_details[0][1].decode() != src_lang:
        return line, lang_details[0][1].decode()

    trans_line = translator(line)

    return trans_line, src_lang


from concurrent.futures import ThreadPoolExecutor


def translate_html_lines(lines, translator, src_lang):
    with ThreadPoolExecutor(max_workers=100) as executor:
        lines_with_tag = list(
            executor.map(lambda l: translate_line_or_not(l, src_lang, translator), lines)
        )

    lines, tags = zip(*lines_with_tag)
    logger.info('translate: %s lines', sum(1 for tag in tags if tag))
    return lines, tags


from itertools import islice
# from collections import namedtuple

# WarcData = namedtuple('WarcData', ['warc_header', 'http_header', 'html_lines', 'trans_html_lines', 'trans_tags'])

from functools import partial
if __name__ == '__main__':
    args = parseargs()
    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)
    gs = goslate.Goslate(executor=concurrent.futures.ThreadPoolExecutor(max_workers=120))

    if args.google_translate:
        src_lang, tgt_lang = args.google_translate
        translator = partial(google_translator, src_lang=src_lang, tgt_lang=tgt_lang)

    elif args.dictionary_translate:
        src_lang, dictionary_file = args.dictionary_translate
        dictionary = dict(reversed(line.split()) for line in open('en-fr.dic', 'r'))
        translator = partial(dictionary_translator, dictionary=dictionary)

    with shelve.open(args.SHELVE) as ted_shelve, fileinput.input(args.FILE) as f:
        for i, (header, warc_header, http_header, html_content) in islice(enumerate(read_warc_file(f)), 0, args.NUM):

            logger.info('Processing page number: %d', i)

            cleaned_html_lines = html_clean(html_content)

            trans_cleaned_html_lines, translate_tags = (
                translate_html_lines(cleaned_html_lines,
                                     translator,
                                     src_lang)
                if args.google_translate or args.dictionary_translate
                else (None, None))

            ted_shelve[header[1]] = (warc_header,
                                     http_header,
                                     cleaned_html_lines,
                                     trans_cleaned_html_lines,
                                     translate_tags)
