import argparse
import sys
import langid
import re
def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-i","--input", help="input file")
  parser.add_argument("-o","--output", help="output file")
  args = parser.parse_args()
  outfile = open(args.output,"w")
  endCount = 0
  totalCount = 0
  langid.set_languages(['en','fr'])
  with open(args.input,"r") as infile:
    for line in infile:
      totalCount += 1
      [url1, url2, eng, fr, score] = line.split("\t")
      if langid.classify(eng)[1] < 0.3 or langid.classify(fr)[1] < 0.3:
      	continue
      if eng == fr:
      	continue
      outfile.write(line)
      endCount += 1 
main()