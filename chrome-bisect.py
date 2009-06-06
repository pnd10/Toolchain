#!/usr/bin/env python2.5
"""
chrome-bisect.py
Copyright (c) 2009, Robert Sesek <http://www.bluestatic.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

BUILD_BASE_URL = "http://build.chromium.org/buildbot/snapshots/chromium-rel-mac"

# Location of the latest build revision number
BUILD_LATEST_URL = "%s/LATEST" % BUILD_BASE_URL

# The location of the builds.
BUILD_ARCHIVE_URL = "/%d/"

# Name of the build archive.
BUILD_ZIP_NAME = "chrome-mac.zip"

# Directory name inside the archive.
BUILD_DIR_NAME = "chrome-mac"

# Name of the executable.
BUILD_EXE_NAME = "Chromium.app"

# URL to the ViewVC commit page.
BUILD_VIEWVC_URL = "http://src.chromium.org/viewvc/chrome?view=rev&revision=%d"

# Revisions below this number will use BUILD_ARCHIVE_URL_ALT
BUILD_ALT_REV = 17731
BUILD_ALT_BASE_URL = "http://build.chromium.org/buildbot/snapshots/sub-rel-mac"

################################################################################

import math
import os
import re
import shutil
import sys
import urllib

# Parses the HTML directory listing into a list of revision numbers.
def parseDirectoryIndex(url):
	handle = urllib.urlopen(url)
	dirindex = handle.read()
	handle.close()
	return re.findall(r'<a href="([0-9]*)/">\1/</a>', dirindex)

# Gets the list of revision numbers between |good| and |bad|.
def getRevList(good, bad):
	# Download the main revlist.
	revlist = parseDirectoryIndex(BUILD_BASE_URL)
	
	# Check to see if we need to use an alternate build archive, too.
	if (good <= BUILD_ALT_REV or bad <= BUILD_ALT_REV):
		revlist += parseDirectoryIndex(BUILD_ALT_BASE_URL)
	
	revlist = map(lambda r: int(r), revlist)
	revlist.sort()
	return revlist

# Downloads revision |rev|, unzips it, and opens it for the user to test.
def tryRevision(rev):
	# Clear anything that's currenlty there.
	try:
		os.remove(BUILD_ZIP_NAME)
		shutil.rmtree(BUILD_DIR_NAME, True)
	except Exception, e:
		pass
	
	# Download the file.
	try:
		if (rev > BUILD_ALT_REV):
			base = BUILD_BASE_URL
		else:
			base = BUILD_ALT_BASE_URL
		urllib.urlretrieve(base + (BUILD_ARCHIVE_URL % rev) + BUILD_ZIP_NAME, BUILD_ZIP_NAME)
	except Exception, e:
		print("Could not retrieve the download. Sorry.")
		sys.exit(-1)
	
	# Unzip the file.
	os.system("unzip -q %s" % BUILD_ZIP_NAME)
	
	# Tell Finder to open the app.
	os.system("open %s/%s" % (BUILD_DIR_NAME, BUILD_EXE_NAME))

# Annoyingly ask the user whether build |rev| is good or bad.
def askIsGoodBuild(rev):
	while True:
		check = raw_input("Build %d [g/b]: " % int(rev))[0]
		if (check == "g" or check  == "b"):
			return (check == "g")
		else:
			print("Just answer the question...")

def main():
	print("chrome-bisect.py: Performs binary search on the continuous builds archive")
	
	# Pick a starting point, try to get HEAD for this.
	badRev = 0
	try:
		nh = urllib.urlopen(BUILD_LATEST_URL)
		latest = int(nh.read())
		nh.close()
		badRev = raw_input("Bad revision [HEAD:%d]: " % latest)
		if (badRev == ""):
			badRev = latest
		badRev = int(badRev)
	except Exception, e:
		print("Could not determine latest revision. This could be a sign of bad things to come...")
		badRev = int(raw_input("Bad revision: "))
	
	# Find out when we were good.
	goodRev = 0
	try:
		goodRev = int(raw_input("Last known good [0]: "))
	except Exception, e:
		pass
	
	# Get a list of revisions to bisect across.
	revlist = getRevList(goodRev, badRev)
	
	# If we don't have a |goodRev|, set it to be the first revision possible.
	if (goodRev == 0):
		goodRev = revlist[0]
	
	# These are indexes of |revlist|.
	good = 0
	bad = len(revlist) - 1
	
	# Binary search time!
	while (good < bad):
		candidates = revlist[good:bad]
		numPoss = len(candidates)
		if (numPoss > 10):
			
			print("%d candidates. %d tries left." % (numPoss, round(math.log(numPoss, 2))))
		else:
			print("Candidates: %s" % revlist[good:bad])
		
		# Cut the problem in half...
		test = int((bad - good) / 2) + good
		testRev = revlist[test]
		
		# Let the user give this revision a spin.
		tryRevision(testRev)
		isGood = askIsGoodBuild(testRev)
		if (isGood):
			good = test + 1
		else:
			bad = test
	
	# We're done. Let the user know the results in an official manner.
	print("You are probably looking for build %d." % revlist[bad])
	print("This is the ViewVC URL for the potential bustage:")
	print(BUILD_VIEWVC_URL % revlist[bad])

if __name__ == '__main__':
	main()
