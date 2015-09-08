#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Generates the daily schedules for the main conference schedule. Amalgamates multiple order
files containing difference pieces of the schedule and outputs a schedule for each day,
rooted in an optionally-supplied directory.

Note: order file must be properly formatted.

Bugs: Workshop and program chairs do not like to properly format order files.

Usage: 

    python order2schedule.py -output_dir auto/papers data/{papers,shortpapers,demos,srw}/order
"""

import re, os
import sys, csv
import argparse
from handbook import *
from collections import defaultdict

PARSER = argparse.ArgumentParser(description="Generate schedules for *ACL handbooks")
PARSER.add_argument("-output_dir", dest="output_dir", default="auto/papers")
PARSER.add_argument('order_files', nargs='+', help='List of order files')
PARSER.add_argument("-debug", action='store_true', default=False, help="Turns on debug information")
args = PARSER.parse_args()

if not os.path.exists(args.output_dir): os.makedirs(args.output_dir)

def debug(m):
    if args.debug:
        print >> sys.stderr, "Debug: %s"%m

cs = ConfSchedule()
for file in args.order_files:
    subconf_name = file.split('/')[1]
    f = open(file)
    cs.parse_order_file( f, subconf_name )
    f.close()
cs.compile_schedule()
# using only cs.dates and cs.schedule from cs

# Now iterate through the combined schedule, printing, printing, printing.
# Write a file for each date. This file can then be imported and, if desired, manually edited.
for date in cs.dates:
    day, num, year = date
    for timerange, events in sorted(cs.schedule[date].iteritems(), cmp=sort_times):
        start, stop = timerange.split('--')

        if not isinstance(events, list):
            continue

        parallel_sessions = filter(lambda x: isinstance(x, Session) and not x.poster, events)
        poster_sessions = filter(lambda x: isinstance(x, Session) and x.poster, events)
        session_num = parallel_sessions[0].num

        if ( len(parallel_sessions) == 1 ) and ( session_num is not None ) and ( len(parallel_sessions[0].get_papers_only() ) > 0 ):
            # I want to deal with those for example for the Best Paper Session
            pass
        elif ( len(parallel_sessions) + len(poster_sessions) == 1 ) or ( session_num == None ):
            debug("skipping session num=%s InParallel=%d"%( session_num, len(parallel_sessions) + len(poster_sessions) ) )
            continue

        if len(parallel_sessions) + len(poster_sessions) > 1:
            path = os.path.join(args.output_dir, '%s-Session-%s.tex' % (day, parallel_sessions[0].num))
            out = open(path, 'w')
            print >> sys.stderr, "\\input{%s}" % (path)

            # PARALLEL SESSIONS
            # Print the Session overview (single-page at-a-glance grid)
            if len(parallel_sessions) > 1:

                # Session with the maximum number of papers
                papers_per_session = [ len(ps.papers) for ps in parallel_sessions]
                max_num_papers = max(papers_per_session)
                s_maxpapers = papers_per_session.index( max(papers_per_session) )
                times = [timef(p.time.split('--')[0]) for p in parallel_sessions[s_maxpapers].papers]

                print >>out, '\\section[Session %s]{Session %s Overview}'%(session_num,  session_num)
                print >>out, '\\begin{center}'
                print >>out, '\\righthyphenmin2 \\sloppy'
                print >>out, '\\begin{tabular}{|p{0.33\\columnwidth}|p{0.33\\columnwidth}|p{0.33\\columnwidth}|}'
                print >>out, '\\hline'
                print >>out, '\\bf Track A & \\bf Track B & \\bf Track C \\\\\\hline'
                print >>out, ' & '.join(["\\it %s"%s.desc for s in parallel_sessions]), '\\\\'
                print >>out, '\\TrackALoc & \\TrackBLoc & \\TrackCLoc \\\\'
                print >>out, '\\hline\\hline'

                for paper_num in xrange(max_num_papers):
                    if paper_num > 0: print >>out, '  \\hline'
                    print >>out, '  \\marginnote{\\rotatebox{90}{%s}}[2mm]' % (times[paper_num])
                    res = []
                    for session in parallel_sessions:
                        if len(session.papers) > paper_num:
                            if session.papers[paper_num].id is None:
                                res.append ('EXT: %s' % ( session.papers[paper_num].title ) )
                            else:
                                res.append ('{%s}\\papertableentry{%s}' % ( session.papers[paper_num].prefix, session.papers[paper_num].id ) )
                        else:
                            res.append("")
                    print >>out, ' & '.join( res )
                    print >>out, '  \\\\'

                print >>out, '\\hline\\end{tabular}\\end{center}\n'
            else:
                debug("skipping index for session <%s> <%s>"% ( parallel_sessions[0].name, parallel_sessions[0].desc )) 

            for track, session in enumerate(poster_sessions, len(parallel_sessions)):
                chair = session.chair()
                print >>out, '\\bigskip{}'
                if chair[1] == '':
                    print >>out, '\\noindent \\textbf{Track %s:} \\emph{%s}\\smallskip{}\n'%(chr(track+65), session.desc)
                else:
                    print >>out, '\\noindent \\textbf{Track %s:} \\emph{%s} \\hfill \\emph{\\sessionchair{%s}{%s}}\\smallskip{}\n'%(
                        chr(track+65), session.desc, chair[0], chair[1] )
                print >>out, '\\noindent {\\PosterLoc \hfill \emph{%s}}'% (timef(session.time))
                print >>out, '\\noindent \\rule[0.5ex]{1\\columnwidth}{1pt}'
                print >>out, '\\begin{itemize}'
                for paper_num in xrange(len(session.papers)):
                    if session.papers[paper_num].id is None:
                        print >>out, '\\item []\\textbf{%s}' % session.papers[paper_num].title
                    else:
                        print >>out, '\\item \\posterlistentry{%s}{%s}' %(session.papers[paper_num].id, session.papers[paper_num].prefix )
                print >>out, '\\end{itemize}\n'
            print >>out, '\\clearpage'
            out.close()

        path = os.path.join(args.output_dir, '%s-Session-%s-abstracts.tex' % (day, parallel_sessions[0].num))
        out = open(path, 'w')
        print >> sys.stderr, "\\input{%s}" % (path)

        if len(parallel_sessions) > 0:
            # Now print the abstracts of the papers in each of the sessions
            # Print the papers
            print >>out, '\\newpage'
            print >>out, '\\section*{Abstracts: Session %s}' % (parallel_sessions[0].num)
            print >>out, '\\bigskip{}'
            for i, session in enumerate(parallel_sessions):
                    chair = session.chair()
                    print >>out, '\\noindent{\\bfseries\\large %s: %s}\\par' % (session.name, session.desc)
                    if chair[1] != '':
                        print >>out, '\\noindent\\Track%cLoc\\hfill\\sessionchair{%s}{%s}\\par' % (chr(i + 65),chair[0],chair[1])
                    else:
                        print >>out, '\\noindent\\Track%cLoc\\hfill\\par' % (chr(i + 65))
                    print >>out, '\\bigskip{}'
                    for paper in session.papers:
                        if paper.id is not None: print >>out, '\\paperabstract{%s}{%s}{%s}' % (paper.id, paper.time, paper.prefix)
                    print >>out, '\\clearpage'
            print >>out, '\n'
        else:
            debug("########## Skipping Abstracts for session <%s> <%s>"% ( session.name, session.desc) ) 

        # POSTER SESSIONS
        for session in poster_sessions:
            chair = session.chair()
            if chair[1] == '':
                print >>out, '\\noindent{\\bfseries\\large %s: %s}\\par' % (session.name, session.desc)
            else:
                print >>out, '\\noindent{\\bfseries\\large %s: %s} \\hfill \\emph{\\sessionchair{%s}{%s}}\\par' % (
                    session.name, session.desc, chair[0], chair[1])
            print >>out, '\\noindent{\\PosterLoc \\hfill \emph{%s}}\\par'% (timef(session.time))
            print >>out, '\\bigskip{}'
            for paper in session.papers:
                if paper.id is not None: print >>out, '\\posterabstract{%s}{%s}' % (paper.id, paper.prefix)
            print >>out, '\\clearpage'
        out.close()





