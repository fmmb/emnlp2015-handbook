#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Matt Post, June 2014

"""
Generates the daily overviews for the main conference schedule. Amalgamates multiple order
iles containing difference pieces of the schedule and outputs a schedule for each day,
rooted in an optionally-supplied directory.

Usage:

 cat data/{papers,shortpapers,demos,srw}/order | order2schedule_overview.py

"""

import re, os
import sys, csv
import argparse
from handbook import *
from collections import defaultdict

PARSER = argparse.ArgumentParser(description="Generate overview schedules for *ACL handbooks")
PARSER.add_argument("-id", dest='id', default="", help="Workshop id. prefix for papers")
PARSER.add_argument("-debug", action='store_true', default=False, help="Turns on debug information")
args = PARSER.parse_args()

def debug(m):
    if args.debug:
        print >> sys.stderr, "Debug: %s"%m

cs = ConfSchedule(overview=True)
if len(args.id) == 0:
    cs.parse_order_file( sys.stdin )
else:
    cs.parse_order_file( sys.stdin, args.id )
cs.compile_schedule()
# using only cs.dates and cs.schedule from cs
    
for ndays, date in enumerate(cs.dates):
    day, num, year = date

    if ndays > 0:
        print "\\vspace{7em}"
    print "\\item[] {\\Large\\bfseries %s, %s, %s}\\\\\\vspace{1ex}"%date

    for timerange, events in sorted(cs.schedule[date].iteritems(), cmp=sort_times):
        start, stop = timerange.split('--')

        if len(events) > 1:
            print >>sys.stderr, "Printing %d existing parallel sessions in sequencial order..."% len(events)

        for event in events:
            if isinstance(event, Session):
                    print  '\n\\vspace{0.75ex}\n\\item[%s--%s] {\\bfseries %s}' % (timef(start), timef(stop), event.title)
                    for p in event.papers:
                        if p.time is not None:
                            start, stop = p.time.split("--")
                            if p.id is None:
                                print  '\n\\vspace{0.5ex}\n\\item[%s--%s] \\textit{%s}' % ( start, stop, p.title )
                            else:
                                print  '\n\\vspace{0.5ex}\n\\item[%s--%s] \\wspaperentry{%s}'% ( start, stop, p.id )
                        else: 
                            if p.id is None:
                                print  '\n\\vspace{0.5ex}\n\\item[$\\bullet$] \\textit{%s}' % (p.title )
                            else:
                                print  '\n\\vspace{0.5ex}\n\\item[$\\bullet$] \\wspaperentry{%s}'% (p.id )
            elif type(event) is str:
                    # A regular event
                    print  '\n\\vspace{0.75ex}\n\\item[%s--%s] {\\bfseries %s}' % (timef(start), timef(stop), event)
            else:
                raise ValueError("Unknown type!!!")

