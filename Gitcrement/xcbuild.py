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

gitcrement = "/Users/rsesek/Library/Shell/bin/gitcrement"

import io, sys, subprocess
from os import environ

if environ["CONFIGURATION"] == "Release":
	subprocess.getoutput(gitcrement + " next")

subprocess.call(["/Users/rsesek/Library/Shell/bin/gitcrement", "current"])

build = subprocess.getoutput(gitcrement + " current")
try:
	build = int(build)
except ValueError:
	build = 0

infopath = environ["CONFIGURATION_BUILD_DIR"] + "/" + environ["INFOPLIST_PATH"]

lastline = ""
plist = ""
f = io.open(infopath, "r")
line = f.readline()
while line != "":
	if lastline.find("CFBundleVersion") != -1:
		plist += ("\t<string>%i</string>\n" % build)
	else:
		plist += line
	lastline = line
	line = f.readline()
f.close()

f = io.open(infopath, "w")
f.write(plist)
f.close()