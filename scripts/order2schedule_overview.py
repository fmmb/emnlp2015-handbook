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
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
PARSER.add_argument("-debug", action='store_true', default=False, help="Turns on debug information")
args = PARSER.parse_args()

if not os.path.exists(args.output_dir): os.makedirs(args.output_dir)

def debug(m):
    if args.debug:
        print >> sys.stderr, "Debug: %s"%m

cs = ConfSchedule(overview=True)
cs.parse_order_file( sys.stdin )
cs.compile_schedule()
# using only cs.dates and cs.schedule from cs
    
for date in cs.dates:
    day, num, year = date
    path = os.path.join(args.output_dir, '%s-overview.tex' % (day))
    out = open(path, 'w')
    print >> sys.stderr, "Writing file", path
    print >>out, '\\renewcommand{\\arraystretch}{1.2}'
    print >>out, '\\begin{SingleTrackSchedule}'
    for timerange, events in sorted(cs.schedule[date].iteritems(), cmp=sort_times):
        start, stop = timerange.split('--')

        if len(events) >= 3:
            # Parallel sessions (assume there are at least 3)
            sessions = [x for x in events]

            # turn "Session 9A" to "Session 9"
            title = 'Session %s' % (sessions[0].num)
            if True:
                oral_sessions = filter(lambda x: isinstance(x, Session) and not x.poster, events)
                poster_sessions = filter(lambda x: isinstance(x, Session) and x.poster, events)
                num_parallel_sessions = len(oral_sessions) + 1

                print >>out, '  %s & -- & %s &' % (timef(start), timef(stop))
                print >>out, '  {\\bfseries %s}\\\\\n' % (title)
                print >>out, ' & \multicolumn{3}{l}{%'
                print >>out, ' \\begin{minipage}[t]{0.94\\linewidth}'
                widths = ['>{\\RaggedRight}p{%.3f\\linewidth}' % (0.94/num_parallel_sessions) for x in range(num_parallel_sessions)]
                print >>out, '  \\begin{tabular}{|%s|}' % ('|'.join(widths))
                print >>out, '  \\hline'
                print >>out, ' & '.join([s.desc for s in oral_sessions]), '&', " \\rule{1\\linewidth}{0.1pt} ".join([p.desc for p in poster_sessions]) , '\\\\'
                rooms = ['\emph{\Track%cLoc}' % (chr(65+x)) for x in range(num_parallel_sessions)]
                print >>out, ' & '.join(rooms), '\\\\'
                print >>out, '  \\hline\\end{tabular}'
                print >>out, '\\end{minipage}'
                print >>out, '}\\\\'
        else:
            for event in events:
                if type(event) is str:
                        # A regular event
                        loc = "\\%sLoc" % ( event.split(' ')[0].capitalize() )
                        debug( "location <%s> for <%s>"%(loc, event) )
                        print >>out, '  %s & -- & %s &' % (timef(start), timef(stop))
                        print >>out, '  {\\bfseries %s} \\hfill \emph{%s}' % (event, loc)
                        print >>out, '  \\\\'
                elif isinstance(event, Session):
                        debug("Session Location <%s> for <%s>"%( event.location(), event.title ) )
                        print >>out, '  %s & -- & %s &' % (timef(start), timef(stop))
                        print >>out, '  {\\bfseries %s} \\hfill \emph{%s}' % (event.title, event.location() )
                        print >>out, '  \\\\'
                        for p in event.papers:
                            if p.time is None:
                                if p.id is None:
                                    print >>out, ' & & & \\textit{%s}\\\\' % ( p.title )
                                else:
                                    print >>out, ' & & & \\paperlistentry{%s}\\\\'% ( p.id )
                            else:
                                start, stop = p.time.split("--")
                                if p.id is None:
                                    print >>out, ' %s & -- & %s & \\textit{%s}\\\\' % ( start, stop, p.title )
                                else:
                                    print >>out, ' %s & -- & %s & \\paperlistentry{%s}\\\\'% ( start, stop, p.id )
                else:
                    raise ValueError("Unknown type!!!")

    print >>out, '\\end{SingleTrackSchedule}'
    out.close()

