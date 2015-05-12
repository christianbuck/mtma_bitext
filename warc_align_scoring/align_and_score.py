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

ScoresAndLines = namedtuple('ScoreAndLines', ['line_equality_ratio', 'jaccard_sim', 'aligned_lines'])

def align_lines_and_score(warc_a, warc_b_tr):
    s = difflib.SequenceMatcher(None, warc_a[2], warc_b_tr[3])

    replace_ranges = [(en_start, en_end, fr_start, fr_end)
                   for op, en_start, en_end, fr_start, fr_end in s.get_opcodes()
                   if op == 'replace' or (op == 'equal' and en_end - en_start == 1)]
#     print(diff_ranges)
    jaccard_sim_sum = 0
    num_vocab = 0
    lines = []

    for en_start, en_end, fr_start, fr_end in replace_ranges:

        # if '\n'.join(warc_b_tr[3][fr_start:fr_end]).lower() == '\n'.join(warc_b_tr[2][fr_start:fr_end]).lower():
            # continue

        words_en = set('\n'.join(warc_a[2][en_start:en_end]).split())
        words_fr = set('\n'.join(warc_b_tr[3][fr_start:fr_end]).split())

        if len(words_en | words_fr) == 0:
            continue
        
        jaccard_sim_sum += len(words_en & words_fr) 
        

        # ratio = difflib.SequenceMatcher(None, words_en, words_fr).ratio()
        # ratio_mean += ratio * len(words_en)

        num_vocab += len(words_en | words_fr)

        # print (ratio)

        lines.extend(
            zip(warc_a[2][en_start:en_end],
                warc_b_tr[3][fr_start:fr_end],
                warc_b_tr[2][fr_start:fr_end]))

    return ScoresAndLines (s.ratio(), jaccard_sim_sum / num_vocab, lines)


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
    # parser.add_argument('-t', '--translate-from', metavar='LANG', dest='SRC_LANG' )

    parser.add_argument('SRC_SHELVE', help='Source shelve database file')
    parser.add_argument('TGT_SHELVE', help='Target shelve database file')
    parser.add_argument('-p', '--print-sentences',  help='Print aliged sentences ', action='store_true')
    parser.add_argument('-v', '--verbose',  help='Produce verbose message', action='store_true')
    return parser.parse_args()



if __name__ == '__main__':
    args = parseargs()
    
    

    logger = get_logger(logging.DEBUG) if args.verbose else get_logger(logging.WARN)

    with shelve.open(args.SRC_SHELVE, 'r') as src_warc, shelve.open(args.TGT_SHELVE, 'r') as tgt_warc:

        for src_url, src_data in src_warc.items():
            best_tgt_url, (line_equality_ratio, jaccard_sim, aligned_lines) = max(
                (
                    ( tgt_url, align_lines_and_score(src_data, tgt_data))
                    for tgt_url, tgt_data in tgt_warc.items()
                ), 
                key = lambda x: x[1].jaccard_sim)
            
            print(' \033[1;32m*\033[m {}\n   --> {}'.format(src_url, best_tgt_url))
            print('   line equality ratio: \033[1;33m{}\033[m\t jaccard sim: \033[1;33m{}\033[m'.format(line_equality_ratio, jaccard_sim)   )
            if args.print_sentences:
                print(*(' en:\t' + en + '\n fren:\t' + fr_to_en + '\n fr:\t' + fr + '\n\n' for en, fr_to_en, fr in aligned_lines))
            
            
            
            
