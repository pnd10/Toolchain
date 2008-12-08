#!/usr/bin/env python

#
# GNU Make Package Receipter
# Copyright (c) 2008, Blue Static <http://www.bluestatic.org>
# 
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU 
# General Public License as published by the Free Software Foundation; either version 2 of the 
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without 
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with this program; if not, 
# write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

RCPT_VERSION = 1

import sys
import os
import stat

def create_index(path):
    """Creates a listing of all the files in the given directory"""
    return _walk_path(path, dict())

def _walk_path(path, index):
    """(PRIVATE) walks down a given path and adds items to the index"""
    
    for f in os.listdir(path):
        pathname = os.path.join(path, f)
        statinfo = os.stat(pathname)
        if stat.S_ISDIR(statinfo[stat.ST_MODE]):
            index.update(_walk_path(pathname, dict()))
        else:
            index[pathname] = statinfo[stat.ST_MTIME]
    
    return index

def create_diff(old, new):
    """Compares two dictionaries, checks the modification date [value] and then returns the mismatching/new ones"""
    result = list()
    for path in new.keys():
        if path in old:
            if new[path] > old[path]:
                result.append(create_entry(path, new[path]))
        else:
            result.append(create_entry(path, new[path]))
    return result

def create_receipt(name, entries):
    """Generates the full XML structure of the receipt file, given the receipt name and the list of entries"""
    xmlout = "<receipt name=\"" + name + "\" version=\"" + str(RCPT_VERSION) + "\">\n\t"
    xmlout += "\n\t".join(entries)
    xmlout += "\n</receipt>"
    return xmlout

def create_entry(path, mtime):
    """Constructs an XML tag given a path name and the mtime"""
    return ("<entry path=\"%s\" mtime=\"%d\" />" % (path, mtime))
    
def main():
    if len(sys.argv) < 3:
    	print("Usage: makercpt.py <install|remove> <name> [<installation path to watch>] [<installation command = 'make install'>]")
    	exit(-1)

    if sys.argv[1] == "install":
    	if len(sys.argv) < 4:
    		print("Usage: makercpt.py install <name> <path> <command = 'make install'>")
    		exit(-1)
	
    	before = create_index(sys.argv[3])
    	os.system("make install" if len(sys.argv) != 5 or sys.argv[4] == "" else sys.argv[4])
    	after = create_index(sys.argv[3])
    	
    	entries = create_diff(before, after)
    	
    	print(create_receipt(sys.argv[2], entries))

if __name__ == "__main__":
    main()
	