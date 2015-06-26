#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from treedist import EditCost, BinaryCosts, MyDOM, build_tree
import base64
from zss import distance

""" produces the .ridx file from a lett file by matching DOM trees """


def debug(l1, l2, d):
    u1 = l1.split("\t")[3]
    u2 = l2.split("\t")[3]
    sys.stderr.write("Dist %s - %s: %f\n" % (u1, u2, d))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument(
        'outfile', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-binary', action='store_true')
    args = parser.parse_args()

    lines_en = []
    lines_fr = []
    for linenr, line in enumerate(args.infile):
        l, mime, enc, url, html, text = line.split("\t")
        html = base64.b64decode(html)
        tree = build_tree(html.split("\n"))
        if tree == None:
            continue

        if l == "en":
            lines_en.append((linenr, tree, line))
        else:
            lines_fr.append((linenr, tree, line))

    for linenr_en, tree_en, line_en in lines_en:

        dists = []
        for linenr_fr, tree_fr, line_fr in lines_fr:
            d = -1
            if args.binary:
                d = distance(tree_en, tree_fr, MyDOM.get_children,
                             BinaryCosts.insert_delete_cost,
                             BinaryCosts.insert_delete_cost,
                             BinaryCosts.update_cost)
            else:
                d = distance(tree_en, tree_fr, MyDOM.get_children,
                             EditCost.remove_cost,
                             EditCost.remove_cost,
                             EditCost.update_cost)
            dists.append((d, linenr_fr, line_fr))

        dists.sort()

        args.outfile.write("%d" % (linenr_en + 1))
        for d, linenr_fr, line_fr in dists[:10]:
            debug(line_en, line_fr, d)
            args.outfile.write("\t%d:%f" % (linenr_fr + 1, d))
        args.outfile.write("\n")
