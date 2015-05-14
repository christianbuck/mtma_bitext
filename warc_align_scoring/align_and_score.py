#!/usr/bin/env python
# -*- coding: utf-8 -*-


import difflib
import argparse
import logging
import shelve
import os.path
from operator import itemgetter
from collections import namedtuple
import sys

ScoresAndLines = namedtuple(
    'ScoreAndLines', ['line_equality_ratio', 'jaccard_sim', 'aligned_lines'])


def align_lines_and_score(warc_src, warc_tgt):
    s = difflib.SequenceMatcher(None, warc_src.html_lines, warc_tgt.trans_html_lines)

    replace_lines = [
        (en_start, en_end, fr_start, fr_end)
        for op, en_start, en_end, fr_start, fr_end in s.get_opcodes()
        if op == 'replace'
        # or (op == 'equal' and en_end - en_start == 1)
    ]
    
    jaccard_sim_sum = 0
    num_vocab = 0
    aligned_lines = []
    for en_start, en_end, fr_start, fr_end in replace_lines:

        src_lines, tgt_lines, tgt_trans_lines = (warc_src.html_lines[en_start:en_end],
                                                 warc_tgt.html_lines[fr_start:fr_end],
                                                 warc_tgt.trans_html_lines[fr_start:fr_end])

        words_src = set('\n'.join(src_lines).lower().split())
        words_tgt = set('\n'.join(tgt_trans_lines).lower().split())

        if len(words_src) == 0 or len(words_tgt)  == 0:
            continue

        jaccard_sim_sum += len(words_src & words_tgt)
        num_vocab += len(words_src | words_tgt)

        aligned_lines.append(
            (
                (en_start, en_end, fr_start, fr_end),
                '\n'.join(src_lines),
                '\n'.join(tgt_lines),
                '\n'.join(tgt_trans_lines),
                
             ))

    return ScoresAndLines(s.ratio(), jaccard_sim_sum / num_vocab, aligned_lines)


def parseargs():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-t', '--translate-from', metavar='LANG', dest='SRC_LANG' )

    parser.add_argument('SRC_SHELVE', help='Source WARC shelve file')
    parser.add_argument('TGT_SHELVE', help='Target translated WARC shelve file')
    parser.add_argument(
        '-p', '--print-sentences',  help='Print aliged sentences ', action='store_true')
    parser.add_argument('-v', '--verbose',  help='Produce verbose message', action='store_true')
    parser.add_argument('-n', '--number',  help='Number of English pages to process', type=int)
    return parser.parse_args()


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

from colored import fg, attr, colored, bg
COLORS = colored('black').paint.keys()
COLOR_STR_MAP = {color.upper() + '_FG': fg(color) for color in COLORS}
COLOR_STR_MAP.update({color.upper() + '_BG': fg(color) for color in COLORS})
COLOR_STR_MAP['RESET'] = attr('reset')

from itertools import islice
WARCData = namedtuple('WARCData', ['warc_header', 'http_header', 'html_lines', 'trans_html_lines', 'trans_tag'])

if __name__ == '__main__':
    args = parseargs()

    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)

    with shelve.open(args.SRC_SHELVE, 'r') as src_data, shelve.open(args.TGT_SHELVE, 'r') as tgt_data:

        for src_url, src_data in islice(src_data.items(), 0, args.number):  # for src_url, src_data from SRC_SHELVE
            src_data = WARCData(*src_data)
            tgt_urls_and_align_results = (
                (tgt_url, align_lines_and_score(src_data, WARCData(*tgt_data)))
                for tgt_url, tgt_data in tgt_data.items())
            
            best_tgt_url, (line_equality_ratio, jaccard_sim, aligned_lines) = max(
                               tgt_urls_and_align_results,
                               key=lambda x: x[1].jaccard_sim)

            print(' {GREEN_FG}*{RESET} {RED_FG}{}{RESET}\n {GREEN_FG}-->{RESET} {BLUE_FG}{}{RESET}'.format(
                src_url, best_tgt_url, **COLOR_STR_MAP))
            print('   line equality ratio: {YELLOW_FG}{}{RESET}  jaccard sim: {YELLOW_FG}{}{RESET}'.format(
                line_equality_ratio, jaccard_sim, **COLOR_STR_MAP))

            if args.print_sentences:
                print(
                    *(
                        (' {YELLOW_FG}--------------{RESET}\n'
                         '{replace_range}\n'
                         '{RED_FG}EN:\n{en}\n\n'
                         '{GREEN_FG}FREN:\n{fr_to_en}\n\n'
                         '{BLUE_FG}FR:\n{fr}\n\n{RESET}'
                         ).format(en=en, fr_to_en=fr_to_en, fr=fr,
                                  replace_range=replace_range, **COLOR_STR_MAP)
                        for replace_range, en, fr_to_en, fr  in aligned_lines))
