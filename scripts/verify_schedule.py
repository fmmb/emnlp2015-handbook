#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Matt Post, May 2014
# Modified by: Fernando Batista, Aug. 2015

# Verifies that the ACLPUB order file is computer-readable.
#
# Usage:
#   cat proceedings/order | python verify-order-file.py
#
# Output is detailed information about errors found in the file.

# 2015-08 changes 
# ------------------
# sessions and breaks, each MUST have a time range. 
#   The generated ACLPUB order file might give it to you formatted correctly for the main conf,
#   but expect trouble and "creativity" from the workshops.
# Need to add support for '!' items (external item), in addition to Day, Session and Break ('*', '+', '=').

import re
import sys

def general_error(lineno, found, expected, eg):
    print 'Format error on line %d' % (lineno)
    print '  ->    found: %s' % found
    print '  -> expected: %s' % expected
    print '     e.g.,', eg

    global error_count
    error_count += 1

TIMERANGE_REGEXP = r'\d+:\d+--\d+:\d+'

def header_error(lineno, line):
    print 'Warning on line %d' % (lineno)
    print '  -> Header lines do not contain time ranges'
    print '  -> Use "=" for headers (display only) and "+" for timed events, e.g.,'
    print '     + 11:00--12:30 Poster Session: Shared Task'
    print '     16  # Paper 1'
    print '     18  # Paper 2'
    print '     ...'

def debug(msg):
    if True:
        print >> sys.stderr, msg

def parse_star(i, line):
    ''' Lines beginning with *
    Days: At the start of each day of the workshop (even if there is only one day).
    Examples:
        * Thursday, June 26, 2015
    '''
    content = line.split(' ',1)[1]
    try:
        day, date, year = content.split(', ')
        month, date = date.split(' ')
    except ValueError:
        general_error(i, line, '* DAY, MONTH DATE, YEAR', 'Thursday, June 26, 2015')
        return

    if day not in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
        general_error(i, day, '* DAY, MONTH DATE, YEAR', 'Thursday, June 26, 2015')
    elif month not in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']:
        general_error(i, month, '* DAY, MONTH DATE, YEAR', 'Thursday, June 26, 2015')
    elif not re.match(r'\d+', date) or int(date) < 1 or int(date) > 31:
        general_error(i, date, '* DAY, MONTH DATE, YEAR', 'Thursday, June 26, 2015')
    elif year != '2015':
        general_error(i, year, '* DAY, MONTH DATE, YEAR', 'Thursday, June 26, 2015')

def parse_plus(i, line):
    '''
    Lines beginning with +
    Events that do not correspond to papers: Breaks, opening remarks, invited talks, panel discussions, awards, etc.
    Examples:
       + 9:00--10:00 Invited Talk by Justine Cassell
    '''
    content = line.split(' ',1)[1]
    try:
       timerange, title = content.split(' ', 1)
       if not re.match(TIMERANGE_REGEXP, timerange):
            general_error(i, timerange, 'HH:MM--HH:MM (time range, 24-hour format, two dashes)', '12:30--13:30')
                
    except ValueError:
        general_error(i, line, '+ HH:MM--HH:MM EVENT TITLE', '+ 14:00-15:30 {\em A Great Talk.} Ellen Elinksy -- Founder, Acme Inc')

def parse_equals(i, line):
    ''' Session titles
    The workshop may be broken up into several sessions. Examples:
        = Session M1R: Machine Learning and Statistical Models
    Now sessions may also have time ranges. Examples:
        = 10:30--11:45 Session 1A: Semantics 1
        = Session 1B: Machine Translation 1
    '''
    content = line.split(' ',1)[1]
    timerange, title = content.split(' ', 1)
    if re.match(TIMERANGE_REGEXP, timerange):
        # debug( "(NEW) Session title with time range: %s"%line )
        pass
    else:
        debug( "(OLD) Session title without time range. Still ok?: %s"%line )

def parse_numbers(i, line):
    ''' 
    Scheduled papers: A typical line contains a paper number followed by a timeslot. 
        An optional comment indicates the first author and title, for your convenience.
    Unscheduled papers: You may omit a paper's timeslot (e.g., in a poster session where the posters run in parallel).
        The paper ID is enough.
        Remember that the order of papers in the order file will determine the order in the proceedings.
    Examples:
        44   # System Combination for Multi-document Summarization
        215 10:30--10:55  # Identifying Political Sentiment between Nation States with Social Media
    '''
    try:
        id, timerange, _ = line.split(' ', 2)
    except ValueError:
        paper_error(i, line)

    if re.match(r'\d', timerange) and not re.match(TIMERANGE_REGEXP, timerange):
        general_error(i, timerange, 'HH:MM--HH:MM (time range, 24-hour format, two dashes)', '12:30--13:30')

def parse_exclamation(i, line):
    '''
    External items
    Examples:
        ! 08:40--09:00 Opening Remarks and Introductory Speeches %by Multiple Speakers
        ! 09:00--10:00 Deep Learning of Semantic Representations %by Yoshua Bengio %u http://www.emnlp2015.org/invited-speakers.html#i1
        ! 11:45--12:10 %ext tacl-final:13
        ! %ext tacl-final:6
        !  Text Mining and NLP Applications %by Poster Presenters
    '''
    content = line.split(' ',1)[1]
    timerange = content.split(' ', 1)[0]
    if re.match(TIMERANGE_REGEXP, timerange):
        debug( "External item with time range: %s"%line )
    else:
        debug( "External item without time range: %s"%line )

    p2 = content.split("%", 1)[1]
    if not p2.startswith("by") and not p2.startswith("ext"):
        general_error(i, line, "! [HH:MM--HH:MM ][title ][%(by ...|ext subconf:papernum)", "multiple examples")
    

error_count = 0
for i, line in enumerate(sys.stdin, 1):
    line = line.rstrip()
    
    if line == '' or line.startswith('#'): # Skip blanks and comments
        pass
    elif line.startswith('* '):
        parse_star(i, line )
    elif line.startswith('+ '):
        parse_plus(i, line )
    elif line.startswith('= '):
        parse_equals(i, line )
    elif re.match(r'^\d+ ', line):
        parse_numbers(i, line )
    elif re.match(r'^\d+/[A-Z]+ ', line):
        debug("(OLD) Probably a TACL paper in the old format. Should this still be used?\n\t%s"%line)
    elif line.startswith('! '):
        parse_exclamation(i, line )
    else:
        general_error(i, line, "Could not parse line", "")
            
print "Found %d errors" % (error_count)
sys.exit(error_count)
