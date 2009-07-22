#!/usr/local/bin/python3.0
"""
Gitcrement
Copyright (c) 2009, Blue Static <http://www.bluestatic.org>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not,
see <http://www.gnu.org/licenses/>.
"""

git = "/usr/local/bin/git"

import os, subprocess, sys
import sqlite3, time
from datetime import datetime

def main():
	if len(sys.argv) < 2:
		sys.exit("Usage: gitcrement [init|current|next|list|info]")
	
	if sys.argv[1] == "init":
		init()
		return
	
	checkDB()
	
	if sys.argv[1] == "current":
		current()
	elif sys.argv[1] == "next":
		next()
	elif sys.argv[1] == "list":
		numlist()
	elif sys.argv[1] == "info":
	  info(int(sys.argv[2]))

SQL = None
def db():
	"""Connects to the database"""
	global SQL
	
	# make sure we're in a git repo
	if subprocess.getoutput(git + " status 1>/dev/null"):
		sys.exit("You are not in a Git repository")
	
	if SQL == None:
		SQL = sqlite3.connect(".gitcrement")
	
	return SQL

def checkDB():
	"""Checks to make sure the database exists"""
	if not os.path.exists(".gitcrement"):
		sys.exit("There is no Gitcrement repository present")

def init():
	"""Initializes the current directory for gitcrement"""
	
	# check for existing db
	if os.path.exists(".gitcrement"):
		sys.exit("A Gitcrement database already exists")
	
	# create the database
	db().execute("""
		CREATE TABLE numbers
		(
			id INTEGER PRIMARY KEY,
			git_hash VARCHAR(40) NOT NULL,
			author VARCHAR(50) NOT NULL,
			datetime INT NOT NULL,
			parent INT NULL REFERENCES versions(id)
		);
	""")
	db().execute("""
		CREATE TABLE project
		(
			key VARCHAR(20) PRIMARY KEY,
			value TEXT NULL
		);
	""")
	db().execute("INSERT INTO project VALUES ('schema_version', '1')")
	db().commit()

def current():
	"""Returns the current version number"""
	print(db().execute("SELECT MAX(id) AS current FROM numbers").fetchone()[0])

def next():
	"""Creates a new build number"""
	git_hash = subprocess.getoutput(git + " rev-list -1 HEAD")
	username = subprocess.getoutput("whoami")
	cur = db().execute("INSERT INTO numbers VALUES (NULL, ?, ?, ?, NULL)", (git_hash, username, int(time.time())))
	db().commit()

def numlist():
	"""Lists all the numbers and who commited them"""
	numbers = db().execute("SELECT * FROM numbers ORDER BY id DESC").fetchall()
	for number in numbers:
		print("%4d: By %s on %s at %s" % (number[0], number[2], datetime.fromtimestamp(number[3]).isoformat(" "), number[1]))

def info(build_num):
  """Gets information on a particular build number"""
  build_info = db().execute("SELECT * FROM numbers WHERE id = ?", (build_num,)).fetchone()
  if not build_info:
    sys.exit("Could not find that build. Sorry.")
  print("--------------------------------- BUILD %d -------------------------------------" % int(build_info[0]))
  print("Build number: %d" % int(build_info[0]))
  print("  Build date: %s" % datetime.fromtimestamp(build_info[3]).isoformat(" "))
  print("    Built by: %s" % build_info[2])
  print("--------------------------------------------------------------------------------")
  print(subprocess.getoutput("git log --no-color -1 %s"  % build_info[1]))
  print("--------------------------------- BUILD %d -------------------------------------" % int(build_info[0]))
  

if __name__ == '__main__':
	main()
