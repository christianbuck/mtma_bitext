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
import argparse
import concurrent.futures
import shelve
from retry import retry
import os.path

def dicTranslate(line):
    return ' '.join(list((french_eng[x] if x in french_eng.keys() else x for x in line.split())))

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
    parser.add_argument('URL')
    parser.add_argument('TOKENIZED_TXT')
    parser.add_argument('SHELVE', help='Output shelve database file')
    parser.add_argument('-v', '--verbose',  help='Produce verbose message', action='store_true')
    return parser.parse_args()


french_eng = {}

if __name__ == '__main__':
    args = parseargs()
    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)
   
    for line in open('en-fr.dic', 'r'):
        en,french = line.split()
        french_eng[french] = en
    
    url_file = open(args.URL, 'r')
    urls = []
    for line in url_file.readlines():
        urls.append(line.strip())

    cnt = -1
    url_text = {}

    # with shelve.open(args.SHELVE) as ted_shelve:
    for line in open(args.TOKENIZED_TXT, 'r'):
        # print(line)
        if(line == "NEW _ ENTRY" + '\n'):
            # print(cnt)
            cnt += 1
            url_text[urls[cnt]] = []
            # ted_shelve[urls[cnt]] = []
            # print(ted_shelve[urls[cnt]])
        else:
            if(args.SRC_LANG == "fr"):
                translated = dicTranslate(line.strip())
                url_text[urls[cnt]].append(translated.strip())
                # print(translated.strip())
            else:
                url_text[urls[cnt]].append(line.strip())
                # print(line.strip())

    with shelve.open(args.SHELVE) as ted_shelve:
        for url in url_text.keys():
            ted_shelve[url] = url_text[url]
            print(ted_shelve[url])
            print('\n')


               
        