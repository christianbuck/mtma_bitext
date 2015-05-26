#!/usr/bin/env python
# -*- coding: utf-8 -*-

import html5lib
import sys
from html5lib import treebuilders, treewalkers
from zss import distance
import chardet
import re


class EditCost(object):

    @staticmethod
    def update_cost(a, b):
        if a.node_type != b.node_type:
            return 10000

        # both nodes have the same type
        if a.label == b.label:
            return 0

        if a.node_type == "tag":
            return 10000  # don't allow 'translation' of tags

        if a.node_type == "meta":
            return 0  # ignore meta for now

        if a.node_type == "chars":
            na, nb = len(a), len(b)
            return 1 - (max(na, nb) + 10.) / (min(na, nb) + 10.)

    @staticmethod
    def remove_cost(a):
        if a.node_type == "tag":
            return 1
        else:
            return len(a) * 0.1


class BinaryCosts(object):

    @staticmethod
    def update_cost(a, b):
        if a.node_type != b.node_type or a.label != b.label:
            return 1
        return 0

    @staticmethod
    def insert_delete_cost(a):
        return 1


class MyDOM(object):

    node_types = {"tag": 0, "chars": 1, "meta": 2}

    def __init__(self, label, node_type, parent=None, depth=0):
        self.label = label
        self.node_type = node_type
        self.children = list()
        self.parent = parent
        self.depth = depth
        self.tokens = self.label.split()
        self.tokenset = set(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def __str__(self):
        pre = "  " * self.depth
        try:
            s = "%s%s:'%s'\n" % (pre, self.node_type,
                                 self.label.encode("utf-8"))
        except:
            print "Bad label: ", repr(self.label)
            sys.exit()

        for c in self.children:
            s += str(c)
        return s

    @staticmethod
    def bracket_notation(node):
        # {} are not allowed in the label
        clean_label = node.label.replace(
            "{", "#").replace("}", "#").replace("\n", " ")
        s = "{ %s:'%s' " % (node.node_type, clean_label.encode("utf-8"))
        for c in node.children:
            s += node.bracket_notation(c)
        s += "} "
        s = re.sub("\s\s+", " ", s)
        return s.replace(" ", "_").replace(':', "_")

    @staticmethod
    def get_children(node):
        return node.children

    @staticmethod
    def get_label(node):
        return node.label

    def get_parent(self):
        return self.parent

    def addkid(self, label, node_type):
        self.children.append(MyDOM(label, node_type, self, self.depth + 1))
        return self.children[-1]


def build_tree(f):
    html = []
    for line in f:
        line = line.replace("\t", "    ")
        html.append(line)
    html = "".join(html)
    encoding = chardet.detect(html)
    # print "Detected encoding: ", encoding
    html = html.decode(encoding["encoding"])

    p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
    dom_tree = p.parse(html)
    walker = treewalkers.getTreeWalker("dom")
    stream = walker(dom_tree)

    chars = ""
    root = MyDOM(u"root", None)
    node = root
    for token in stream:
        token_type = token.get("type", None)
        
        if token_type.endswith("Error"):
            return None

        if token_type == "Comment":  # ignore comments for now
            continue

        if token_type.endswith("Characters"):
            chars += token.get("data", "")
            continue

        if chars.strip():
            node.addkid(chars, "chars")
        chars = ""

        tag_name = token.get("name", None)

        if token_type == "EmptyTag":
            continue
            node.addkid(tag_name, "tag")
            for k, v in token.get("data", {}).iteritems():
                node.addkid("%s:%s" % (k[1], v), "meta")
            continue

        assert tag_name is not None, token
        tag_name = tag_name.upper()

        if token_type == "EndTag":
            assert MyDOM.get_label(node) == tag_name, token
            node = node.get_parent()
            assert node is not None, "Unbalanced Tree"

        if token_type == "StartTag":
            node = node.addkid(tag_name, "tag")

    return root


def fix_bracket_format(s):
    return re.sub(r"[^a-zA-Z0-9\{\}]+", r"", s)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=argparse.FileType('r'),
                        help='source corpus')
    parser.add_argument('target', type=argparse.FileType('r'),
                        help='target corpus')
    parser.add_argument('-writetrees', type=argparse.FileType('w'),
                        help='write trees in bracket notation')
    parser.add_argument('-binary', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    source_tree = build_tree(args.source)
    target_tree = build_tree(args.target)

    if args.writetrees:
        args.writetrees.write(
            fix_bracket_format(MyDOM.bracket_notation(source_tree)))
        args.writetrees.write("\n")
        args.writetrees.write(
            fix_bracket_format(MyDOM.bracket_notation(target_tree)))
        sys.exit()

    if args.binary:
        print distance(source_tree, target_tree, MyDOM.get_children,
                       BinaryCosts.insert_delete_cost,
                       BinaryCosts.insert_delete_cost,
                       BinaryCosts.update_cost)
    else:
        print distance(source_tree, target_tree, MyDOM.get_children,
                       EditCost.remove_cost,
                       EditCost.remove_cost,
                       EditCost.update_cost)
