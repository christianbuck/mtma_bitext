#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import argparse
import shelve
import sys


def parseargs():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-t', '--translate-from', metavar='LANG', dest='SRC_LANG' )

    parser.add_argument('SHELVE', help='WARC shelve file')
    parser.add_argument('RANGE', nargs='*',
                        help='Range ("3" or "2-5")', default=['1'])

    return parser.parse_args()





def range_to_page_numbers(page_ranges):

    pages = []
    for page_range in page_ranges:
        start, *end = page_range.split('-', 1)

        try:
            if not end:
                pages.append(int(start))
            else:
                pages.extend(range(int(start), int(end[0]) + 1))

        except ValueError:
            print('Range Error:', page_range, file=sys.stderr)
            sys.exit(1)
    return pages

from colored import fg, attr, colored, bg
COLORS = colored('black').paint.keys()
COLOR_STR_MAP = {color.upper() + '_FG': fg(color) for color in COLORS}
COLOR_STR_MAP.update({color.upper() + '_BG': fg(color) for color in COLORS})
COLOR_STR_MAP['RESET'] = attr('reset')


WARCData = namedtuple(
    'WARCData', ['warc_header', 'http_header', 'html_lines', 'trans_html_lines', 'trans_tag'])


from itertools import islice
if __name__ == '__main__':
    args = parseargs()
    
    pages = frozenset(range_to_page_numbers(args.RANGE))
    
    with shelve.open(args.SHELVE, 'r') as warc_data:
        for i, (url, data) in enumerate(warc_data.items()):
            data = WARCData(*data)
            if i in pages:
                print('{RED_FG}== WARC HEADER =={RESET}'.format(**COLOR_STR_MAP))
                # print('\n {GREEN_FG}*{RESET}'.format(**COLOR_STR_MAP))
                print(data.warc_header)
                print('{RED_FG}== HTTP HEADER =={RESET}'.format(**COLOR_STR_MAP))
                # print('\n {GREEN_FG}*{RESET}'.format(**COLOR_STR_MAP))
                print(data.http_header)
                print('{RED_FG}== HTML LINES =={RESET}'.format(**COLOR_STR_MAP))
                
                if data.trans_html_lines:
                    for html, trans_html, trans_tag in zip(data.html_lines, data.trans_html_lines, data.trans_tag):
                        print('{GREEN_FG}----- {} ------ {RESET}'.format(trans_tag, **COLOR_STR_MAP))
                        print('{YELLOW_FG} F - {RESET}{}'.format(html, **COLOR_STR_MAP))
                        print('{BLUE_FG} E - {RESET}{}'.format(trans_html, **COLOR_STR_MAP))
                        
                else:
                    for html in data.html_lines:
                        print('{YELLOW_FG} F - {RESET}{}'.format(html, **COLOR_STR_MAP))


                
                
                
                
