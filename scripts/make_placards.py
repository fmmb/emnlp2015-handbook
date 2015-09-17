#!/usr/bin/env ipython
# -*- coding: utf-8 -*-
# Matt Post, June 2014
# Fernando Batista, September 2015

"""
Generates the placards posted outside each room listing the sessions hosted there.

Usage:

  make_placards.py papers shortpapers tacl srw

Generates files in auto/placards, one for each session+day.

"""

import re
import os
import sys
import codecs
import argparse
import jinja2
from collections import defaultdict
from paper_info import Paper
from handbook import *

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

PARSER = argparse.ArgumentParser(description="Generate overview schedules for *ACL handbooks")
PARSER.add_argument("subconferences", nargs='+')
PARSER.add_argument("-template", dest="template", default='misc/placard.jinja2', help="location of Jinja2 LaTeX template")
PARSER.add_argument("-output_dir", dest="output_dir", default="misc/placards")
PARSER.add_argument("-logo", dest="logo", default="content/images/EMNLP-2015-Logo.jpg")
PARSER.add_argument("-debug", action='store_false', default=True, help="Turns on debug information")
args = PARSER.parse_args()

if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)

def debug(m):
    if args.debug:
        print >> sys.stderr, "Debug: %s"%m

def timef(time):
    return time

def timerangef(timerange):
    return '--'.join(map(timef, timerange.split('--')))

def sort_times2(a, b):
    if not ( re.search("--", a['time']) and re.search("--", b['time']) ):
        return True
    ahour, amin = a['time'].split('--')[0].split(':')
    bhour, bmin = b['time'].split('--')[0].split(':')
    if ahour == bhour:
        return cmp(int(amin), int(bmin))
    return cmp(int(ahour), int(bhour))

class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

sessions = Vividict()

class CollectionOfSessions:
    def __init__(self):
        self.sessions = {}

    def add(self, date, room, name, info):
        #print "ADDING:", date, room, name
        if not self.sessions.has_key(date):
            self.sessions[date] = {}
        if not self.sessions[date].has_key(room):
            self.sessions[date][room] = {}
        if not self.sessions[date][room].has_key(name):
            self.sessions[date][room][name] = info 
            self.sessions[date][room][name]['papers'] = [] 
            if re.search("poster", info['title'], re.I):
                self.sessions[date][room][name]['posters'] = True
                self.sessions[date][room][name]['poster_id'] = 1
            else:
                self.sessions[date][room][name]['posters'] = False
        else:
            debug("Error: Session already exists")

    def exists(self, date, room, name):
        if not self.sessions.has_key(date):
            return False
        if not self.sessions[date].has_key(room):
            return False
        if not self.sessions[date][room].has_key(name):
            return False
        return True

    def add_paper(self, date, room, name, info):
        if not self.exists(date, room, name):
            raise ValueError("Session does not exist")
        if ( info['time'] == "" ) and self.sessions[date][room][name]['posters']:
            info['time'] = "\\hfill{}%s-%d"% ( self.sessions[date][room][name]['track'], self.sessions[date][room][name]['poster_id'] )
            self.sessions[date][room][name]['poster_id'] += 1
        self.sessions[date][room][name]['papers'].append(info)

class MyPaper:
    def __init__(self, line, subconf):
        self.line = line
        self.id = None
        self.time = ""
        self.poster = True
        self.prefix = "" # Important for compatibility issues
        self.subconf = subconf

        self.id, content = line.split(' ', 1)
        if re.search(r'^\d+', content) is not None:
            self.time, comment = content.split(' ', 1)
            self.time = timerangef(self.time)
            self.poster = False
        else:
            comment = content

    def __str__(self):
        return "id=%s time=%s poster=%s prefix=%s" % (self.id, self.time, self.poster, self.prefix)

class MyExternalItem:
    ''' Examples:
            ! 10:30--12:10 Long Paper Cluster 1: Summarization (P1-4) %by Poster Presenters
            ! 11:45--12:10 %ext tacl-final:3
            ! %ext tacl-final:6
    '''
    def __init__(self, line, subconf):
        self.line = line
        self.id = None     # if remains None we can conclude is the first example above
        self.time = ""     # if remains None then we are talking about the 3rd example
        self.poster = True # 2nd example occurs when ID and TIME are not NONE
        self.title = None
        self.prefix = ""
        self.subconf = subconf
        self.authors = ""

        content = line.split(' ', 1)[1]
        if re.search(r'^\d+', content) is not None:
            self.time, rest = content.split(' ', 1)
            self.time = timerangef(self.time)
            self.poster = False
            if not validate_time(self.time): raise ValueError("Incorrect value for time <%s>"% self.time)
            content = rest

        keys = extract_keywords(content)
        self.title = extract_title(content)
        if keys.has_key('ext'):
            tokens = keys['ext'].split(':')
            self.subconf = tokens[0]
            self.id = tokens[1]
            if tokens[0] == "tacl-final": self.prefix = "[TACL] "
        elif keys.has_key('by'):
            self.title =  self.title.strip()
            self.authors = keys['by']
            self.poster = False
        

    def __str__(self):
        return "%s %s %s %s %s" % (self.id, self.time, self.poster, self.title, self.prefix)

mysessions = CollectionOfSessions()
for subconf in args.subconferences:
    for line in open('data/%s/order' % subconf):
        line = line.rstrip()

        ##print "LINE", line
        if line.startswith('*'):
            day, date, year = line[2:].split(', ')
            daydate = '%s, %s' % (day, date)
            
        elif line.startswith('='):
            line = line.split(" ",1)[1]
            kw = extract_keywords(line)
            session_name = line.split("#",1)[0]
            match = re.search(r'Session \d+([A-Z])|Session ([A-Z])\d+', session_name)
            if (match is not None) and kw.has_key("room"):
                session_track = match.group(1)
                session_room = kw['room']
                session_name = re.sub("\([^(]+\)\s*$","", session_name)
                session_info = { 'date': daydate, 'title': session_name, 'track': session_track, 'room': session_room, 'chair': kw.get('chair1') }
                mysessions.add(daydate, session_room, session_name, session_info )
            else:
                print >> sys.stderr, "Skipping session: %s"% line

        elif line.startswith('!'):
            item = MyExternalItem(line, subconf)
            if item.id is not None:
                p = Paper('data/%s/final/%s/%s_metadata.txt' % (item.subconf, item.id, item.id))
                paper_info = {'time': item.time, 'title': "%s%s"% (item.prefix, p.escaped_title()), 'authors': (', '.join(map(unicode, p.authors))) } 
                mysessions.add_paper(daydate, session_room, session_name, paper_info )
            else:
                paper_info = {'time': item.time, 'title': item.title, 'authors': item.authors }
                mysessions.add_paper(daydate, session_room, session_name, paper_info )

        elif re.match(r'\d+ ', line):
            if not mysessions.exists(daydate, session_room, session_name):
                raise ValueError("Session does not exist")
            
            item = MyPaper( line, subconf )

            p = Paper('data/%s/final/%s/%s_metadata.txt' % (item.subconf, item.id, item.id))
   
            paper_info = {'time': item.time, 'title': p.escaped_title(), 'authors': (', '.join(map(unicode, p.authors))) } 
            mysessions.add_paper(daydate, session_room, session_name, paper_info )

#sys.exit(0)
templateEnv = jinja2.Environment(loader = jinja2.FileSystemLoader( searchpath="." ))
template = templateEnv.get_template(args.template)

for day, data in mysessions.sessions.iteritems():
    for room in data.keys():

        all_data = {
            'date': day,
            'sessions': [],
            'room': room,
        }

        for session in sorted(data[room].keys()):
            all_data['sessions'].append({
                'title': session,
                'papers': sorted(data[room][session]['papers'], lambda x,y: sort_times2(x,y))
            })
        fname = '%s/%s-%s.tex' % (args.output_dir, re.sub(", | ","-", day) , re.sub(" ","-", room) )
        out = codecs.open(fname , 'w', 'utf-8')
        out.write(template.render(all_data))
        out.close()
        print "wrote: %s"% fname
