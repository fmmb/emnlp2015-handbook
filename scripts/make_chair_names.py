#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Fernando Batista, September 2015

import re
import os
import sys
import codecs
import argparse
from collections import defaultdict
from paper_info import Paper
from handbook import *

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

PARSER = argparse.ArgumentParser(description="Generates the placards for each chair, to put in their table")
PARSER.add_argument("orderfiles", nargs='+')
PARSER.add_argument("-debug", action='store_false', default=False, help="Turns on debug information")
args = PARSER.parse_args()

def debug(m):
    if args.debug:
        print >> sys.stderr, "Debug: %s"%m

print '''\\documentclass[english]{article}
\\usepackage[T1]{fontenc}
\\usepackage[latin9]{inputenc}
\\usepackage[a4paper]{geometry}
\\geometry{verbose,tmargin=2cm,bmargin=2cm,lmargin=3cm,rmargin=3cm}
\\pagestyle{empty}
\\usepackage{graphicx}
\\begin{document}
'''
for order in args.orderfiles:
    for line in open(order):
        line = line.rstrip()

        if line.startswith('*'):
            day, date, year = line[2:].split(', ')
            
        elif line.startswith('='):
            line = line.split(" ",1)[1]
            kw = extract_keywords(line)
            session_name = line.split("#",1)[0]
            if kw.has_key("chair1"):
                session_name = re.sub("\([^(]+\)\s*$","", session_name)
                print '\\rotatebox{-90}{%'
                print '\\begin{minipage}[t][0.45\\textwidth]{0.95\\textheight}%'
                print '\\resizebox{1\\textwidth}{!}{%s}'% kw['chair1']
                print '\\vfill{}'
                print '%s, %s\\hfill{}%s'% (day, session_name, kw.get('room') )
                print '\\end{minipage}}'
                print '\\newpage'
            else:
                debug("Skipping session: %s"% line)

print '\\end{document}'
