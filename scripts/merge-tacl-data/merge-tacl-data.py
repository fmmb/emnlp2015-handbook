#!/usr/bin/env python

import sys
import re

def get_tacl_ids(schedule_csv):
    result = []
    tacl_re = re.compile(r".*tacl-final:(\d+).*")
    with open(schedule_csv, "r") as inf:
        for line in inf:
            line = line.strip()
            match = tacl_re.match(line)
            if match:
                result.append(int(match.group(1)))
    return result
                
def merge_tacl_data(lines, schedule_csv):
    result = []
    tacl_ids = get_tacl_ids(schedule_csv)
    tacl_re = re.compile(r"(.+)\[TACL\].*")
    assert len(tacl_ids) == 17
    offset = 0
    for line in lines:
        line = line.strip()
        match = tacl_re.match(line)
        if not match:
            result.append(line)
        else:
            result.append("{0}%ext tacl-final:{1}".format(match.group(1), tacl_ids[offset]))
            offset += 1
    assert offset == len(tacl_ids)
    return result

def fix_poster_sessions(lines):
  ''' Groups: 
  - Time range
  - Session code
  - Range of papers
  - Cluster title
  - Session type
  - Comments
  E.g: = 10:30--12:10 Session 1D (P1-4): Summarization (Long Paper Posters) # %room Lower Level Foyer
  '''
  poster_re = re.compile(r"= ([0-9:-]+) Session ([0-9a-zA-Z]+) (\(P[0-9-]+\)): (.+?) \((.+?) Posters\) (.*)")
  last_session_letter = "X"
  cluster_offset = 1
  result = []
  for line in lines:
    match = poster_re.match(line)
    if match:
      time, code, papers, title, poster_type, comments = match.groups()
      current_session_letter = code[-1]
      if current_session_letter != last_session_letter:
        result.append("= {0} Session {1}: {2} Posters {3}".format( time, code, poster_type, comments))
        cluster_offset = 1
      result.append("! {0} Poster Cluster {2}: {3} {4} %by Poster Presenters".format(time, poster_type, cluster_offset, title, papers))
      cluster_offset += 1
      last_session_letter = current_session_letter
    else:
      result.append(line)
  return result

def fix_other_stuff(lines):
    registration_re = re.compile(r"=.*Registration.*")
    for i in xrange(len(lines)):
        match = registration_re.match(lines[i])
        if match:
            lines[i] = lines[i].replace('=', '+', 1)
    return lines         


if __name__ == "__main__":
    order_file = sys.argv[1]
    schedule_tsv = sys.argv[2]
    lines = []
    with open(order_file) as inf:
        lines.extend(x.strip() for x in inf.readlines())
    lines = merge_tacl_data(lines, schedule_tsv)
    lines = fix_poster_sessions(lines)
    lines = fix_other_stuff(lines)
    print "\n".join(lines)
    

