# -*- coding: utf-8 -*-

import re
import sys
from collections import defaultdict
from csv import DictReader

def time_min(a, b):
    ahour, amin = a.split(':')
    bhour, bmin = b.split(':')
    if ahour == bhour:
        if amin < bmin:
            return a
        elif amin > bmin:
            return b
        else:
            return a
    elif ahour < bhour:
        return a
    else:
        return b

def time_max(a, b):
    if time_min(a, b) == a:
        return b
    return a

def validate_time(t):
    if re.match(r'[0-9]{2}:[0-9]{2}--[0-9]{2}:[0-9]{2}', t):
        return True
    return False

def sort_times(a, b):
    ahour, amin = a[0].split('--')[0].split(':')
    bhour, bmin = b[0].split('--')[0].split(':')
    if ahour == bhour:
        return cmp(int(amin), int(bmin))
    return cmp(int(ahour), int(bhour))

def timef(time):
    return time

def minus12_deactivated(time):
    if "--" in time:
        return '--'.join(map(lambda x: minus12(x), time.split('--')))

    hours, minutes = time.split(':')
    if hours.startswith('0'):
        hours = hours[1:]
    if int(hours) >= 13:
        hours = `int(hours) - 12`

    return '%s:%s' % (hours, minutes)

def extract_keywords(title):
    """Extracts keywords from a title, and returns a dictionary of keys and values"""
    dict = {}
    for key, value in re.findall('%(\w+) ([^%]+)', title):
        if ( key == "by" ) and re.match('(Multiple Speakers|Poster Presenters)', value.strip(), re.I):
            pass
        else:
            dict[key] = value.strip()
    return dict

def extract_title(title):
    """Returns the title"""
    if title.find('#') != -1:
        title = title[:title.find('#')].strip()
    if title.find('%') != -1:
        title = title[:title.find('%')].strip()
    return title
        
def latex_escape(str):
    """Replaces unescaped special characters with escaped versions, and does
    other special character conversions."""
    
    str = str.replace('~','{\\textasciitilde}')
#    str = str.replace('β','\\beta')

    # escape these characters if not already escaped
    special_chars = r'\#\@\&\$\_\%'
    patternstr = r'([^\\])([%s])' % (special_chars)
    str = re.sub(patternstr, '\\1\\\\\\2', str)

    # fix superscripts
#    str = re.sub(r'([^$])\^(.*?) ', r'\1$^\2$ ',  str)
    return str

def threedigits(str):
    return '%03d' % (int(str))

class PaperItem:
    def __init__(self, line, subconf):
        self.line = line
        self.id = None
        self.time = None
        self.poster = True
        self.prefix = "" # Important for compatibility issues

        self.id, content = line.split(' ', 1)
        if re.search(r'^\d+', content) is not None:
            self.time, comment = content.split(' ', 1)
            self.poster = False
        else:
            comment = content

        if self.id.find('/') != -1:
            tokens = self.id.split('/')
            self.id = '%s-%s' % (tokens[1].lower(), threedigits(tokens[0]))
        else:
            self.id = '%s-%s' % (subconf, threedigits(self.id))
            
    def __str__(self):
        return "id=%s time=%s poster=%s prefix=%s" % (self.id, self.time, self.poster, self.prefix)

class ExternalItem:
    ''' Examples:
            ! 10:30--12:10 Long Paper Cluster 1: Summarization (P1-4) %by Poster Presenters
            ! 11:45--12:10 %ext tacl-final:3
            ! %ext tacl-final:6
    '''
    def __init__(self, line):
        self.line = line
        self.id = None     # if remains None we can conclude is the first example above
        self.time = None   # if remains None then we are talking about the 3rd example
        self.poster = True # 2nd example occurs when ID and TIME are not NONE 
        self.title = None
        self.prefix = "" 

        content = line.split(' ', 1)[1]
        if re.search(r'^\d+', content) is not None:
            self.time, rest = content.split(' ', 1)
            self.poster = False
            if not validate_time(self.time): raise ValueError("Incorrect value for time <%s>"% self.time)
            content = rest

        keys = extract_keywords(content)
        self.title = extract_title(content)
        if keys.has_key('ext'):
            tokens = keys['ext'].split(':')
            self.id = '%s-%s' % ( tokens[0], threedigits( tokens[1] ) )
            if tokens[0] == "tacl-final": self.prefix = "[TACL] "
        elif keys.has_key('by'):
            self.title = "%s (%s)" % (self.title.strip(), keys['by'])
            self.poster = False
        #print >> sys.stderr, "DEBUG: External Item ID:%s TIME:%s POSTER:%s Prefix:%s Title:%s" % (self.id, self.time, self.poster, self.prefix, self.title)    
            
    def __str__(self):
        return "%s %s %s %s %s" % (self.id, self.time, self.poster, self.title, self.prefix)

class Session:
    ''' Examples:
    = 10:30--12:10 Session 1D (P1-4): Summarization (Long Paper Posters) # %room Lower Level Foyer
    '''
    def __init__(self, line, date):
        self.line = line
        _, self.time, namestr = line.split(' ', 2)
        self.keywords = extract_keywords(namestr)
        self.title = extract_title(namestr)
   
        self.poster = False
        if re.search(r'best paper session|demo|poster', self.title, re.I):
            self.poster = True

        self.desc = None
        self.num = None
        self.name = None
        if self.title.find(':') == -1:
            self.desc = self.title
        else:
            self.name, self.desc = [ i.strip() for i in self.title.split(':', 1)]
            if re.search(r" ([0-9]+)[A-Z]( |$)", self.name, re.I):
                m = re.search(r" ([0-9]+)[A-Z]( |$)", self.name, re.I)
                self.num = m.groups()[0]
            elif re.search(r" ([A-Z][0-9]+)( |$)", self.name, re.I): # Plenary sessions P1, P2, ...
                m = re.search(r" ([A-Z][0-9]+)( |$)", self.name, re.I)
                self.num = m.groups()[0]
            elif re.search(r" ([0-9]+)( |$)", self.name, re.I): # Workshop sessions
                m = re.search(r" ([0-9]+)( |$)", self.name, re.I)
                self.num = m.groups()[0]
            else:
                print >>sys.stderr, "Warning: Could not parse session number from: <%s>\n\tline: %s"% (self.name, line)

        self.date = date
        self.papers = []
        #print >> sys.stderr, line, "\n\tNAME:", self.name, "DESC:", self.desc, "NUM:", self.num, "POSTER:", self.poster, "TITLE:", self.title, "KWORDS:", self.keywords

    def location(self):
        if self.keywords.has_key("room"):
            return self.keywords["room"] 
        elif self.desc is None:
            return "\\UnknownLoc"
        elif self.desc.find(" "):
            return "\\%sLoc"% ( self.desc.split(' ')[0].capitalize() )
        else:
            return "\\%sLoc"% ( event.desc.capitalize() )

    def __str__(self):
        return "SESSION NUM:%s DATE:%s TIME:%s NAME:%s DESC:%s" % (self.num, self.date, self.time, self.name, self.desc)

    def add_paper(self,paper):
        self.papers.append(paper)

    def get_papers_only(self):
        return [p for p in self.papers if isinstance(p, PaperItem)]
        
    def chair(self):
        """Returns the (first name, last name) of the chair, if found in a %chair keyword"""
        
        if self.keywords.has_key('chair1'):
            fullname = self.keywords['chair1']
            if ',' in fullname:
                names = fullname.split(',')
                return (names[1].strip(), names[0].strip())
            elif fullname.find(" ") >= 0:
                # This is just a heuristic, assuming the first name is one word and the last
                # name is 1+ words
                names = fullname.split(' ', 1)
                return (names[0].strip(), names[1].strip())
            else:
                return (fullname.strip(), "")
        else:
            return ('', '')


class ConfSchedule:
    def __init__(self, overview=False):
        self.overview = overview
        self.dates = []
        self.schedule = defaultdict(defaultdict)
        self.sessions = defaultdict()

    def parse_order_file(self, f=sys.stdin, subconf_name="papers"):
        for line in f:
            line = line.rstrip()
            # print "LINE", line

            if line.startswith("#"):
                # Letting repeated papers to appear anyway. Example:
                #  #662 09:05--09:30 # NOTE: PAPER PRESENT MORE THAN ONCE IN THE SCHEDULE  # Broad-coverage CCG
                line = line[1:]
                
            if line.startswith('*'):
                # This sets the day
                day, date, year = line[2:].split(', ')
                if not (day, date, year) in self.dates:
                    self.dates.append((day, date, year))
                session_name = None

            elif line.startswith('='):
                # This names a parallel session that runs at a certain time
                timerange, session_name = line[2:].split(' ', 1)
                if not validate_time(timerange):
                    raise ValueError("Error in time range format <%s>"%timerange)
                
                if self.sessions.has_key(session_name):
                    raise ValueError("Session <%s> already exists" % session_name )

                self.sessions[session_name] = Session(line, (day, date, year))

            elif re.match(r'^\d+', line) is not None:
                id, rest = line.split(' ', 1)
                if re.match(r'^\d+:\d+-+\d+:\d+', rest) is not None:
                    title = rest.split(' ', 1)
                else:
                    title = rest

                if not self.sessions.has_key(session_name):
                    # FMMB: This should never be happening
                    raise ValueError

                self.sessions[session_name].add_paper(PaperItem(line, subconf_name))

            elif line.startswith('!'):
                if not self.sessions.has_key(session_name): raise ValueError("Session name should be set <%s>"%session_name)
                self.sessions[session_name].add_paper( ExternalItem(line) )

            elif line.startswith('+'):
                timerange, title = line[2:].split(' ', 1)
                if not validate_time(timerange):
                    raise ValueError("Error in time range format <%s>"%timerange)

                if self.overview:
                    keys = extract_keywords(title)
                    title = extract_title(title)
                    if keys.has_key('by'):
                        title = "%s (%s)" % (title.strip(), keys['by'])

                    if not self.schedule[(day, date, year)].has_key(timerange):
                        self.schedule[(day, date, year)][timerange] = []
                    self.schedule[(day, date, year)][timerange].append(title)

                else:
                    if re.search(r'best paper session|demo|poster', title, re.I):
                        print >> sys.stderr, "DEBUG: I Don't this this ever happens... At least in EMNLP2015"
                        session_name = title
                        self.sessions[session_name] = Session(line, (day, date, year))
            else:
                raise ValueError("Cannot parse line: %s"%line)

    def compile_schedule(self):
        # Take all the sessions and place them at their time
        for session in sorted(self.sessions.keys()):
            day, date, year = self.sessions[session].date
            timerange = self.sessions[session].time
            #print >> sys.stderr, "SESSION", session, day, date, year, timerange
            if not self.schedule[(day, date, year)].has_key(timerange):
                self.schedule[(day, date, year)][timerange] = []
            self.schedule[(day, date, year)][timerange].append(self.sessions[session])



















