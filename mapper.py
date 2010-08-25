#!/usr/bin/env python2.6

"""
srcer (a.k.a. Mapper)

srcer is a command-line wrapper for svn. If you've ever found yourself typing
long svn URL's to perform server-side operations, you can use srcer to simplify
your life.

srcer maps kewords to SVN urls, so that instead of typing:
  $ svn lock svn://svn.chromium.org/chrome/trunk/src/chrome/app/nibs/Preferences.xib
You can type:
  $ srcer lock //chrome/chrome/app/nibs/Preferences.xib

To add a keyword, type:
  $ srcer -add chrome svn://svn.chromium.org/chrome/trunk/src
To remove:
  $ srcer -rm chrome
To list:
  $ srcer -ls

It's that simple.
"""

import json
import os
import re
import sys

MAP_PATH = os.path.expanduser("~/.src_mapper")

def ReplaceArgs(name_map, args):
  """Iterates over the name map and replaces any keywords."""
  for name in name_map:
    args = map(lambda a: re.sub(r'^//' + name + '(/|$)', name_map[name] + '/', a), args)
  return args

# srcer always takes at least 2 args.
if len(sys.argv) < 2:
  print "srcer -ls, -add name url, -rm name, svn_command //keyword/url"
  sys.exit()

# Try loading the map into memory.
if os.path.exists(MAP_PATH):
  map_fp = open(MAP_PATH, 'r')
  MAP = json.load(map_fp)
  map_fp.close()
else:
  MAP = {}

# srcer -add name url
if sys.argv[1] == "-add":
  if len(sys.argv) != 4:
    print "add <name> <url>"
    sys.exit(1)
  MAP[sys.argv[2]] = sys.argv[3]

  map_fp = open(MAP_PATH, 'w')
  json.dump(MAP, map_fp, indent=2)
  map_fp.close()

# srcer -rm name
elif sys.argv[1] == "-rm":
  if len(sys.argv) != 3:
    print "rm <name>"
    sys.exit(1)
  del MAP[sys.argv[2]]
  
  map_fp = open(MAP_PATH, 'w')
  json.dump(MAP, map_fp, indent=2)
  map_fp.close()

# srcer -ls
elif sys.argv[1] == "-ls":
  max_len = 0
  for name in MAP:
    if len(name) > max_len:
      max_len = len(name)
  
  print 'SOURCE MAPPINGS:'
  for name in MAP:
    print '  ' + name.rjust(max_len) + ' : ' + MAP[name]

# Execute command
else:
  args = ['svn']
  args.extend(ReplaceArgs(MAP, sys.argv[1:]))
  os.execvp('svn', args)