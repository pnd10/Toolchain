#!/usr/bin/env python
"""
git-svn-sync.py
Copyright (c) 2010, Robert Sesek <http://www.bluestatic.org>

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

"""
git-svn Sync:

This program is an extension to git-svn-rebase that performs an checkout of
svn:external definitions. Place this in PATH and run it from any git repository
with that is cloned from SVN. Running this will perform a git-svn-rebase and
will then update exteranls.

The external checkouts can be either svn working copies, full git repositories,
or shallow (no history) git repositories. The default is a full git repository.

Usage:

cd to/some/git-svn/repo/
git svn sync -t [svn|git|shallow]
"""

import optparse
import os
import os.path
import subprocess
import sys

def GitRepoPath():
  """Returns the git repository root path."""
  get_path = subprocess.Popen(["git", "rev-parse", "--show-cdup"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  get_path.wait()
  if get_path.stderr.readline():
    return None
  return os.path.abspath(os.path.join(os.getcwd(), get_path.stdout.readline().strip()))

def IsGitSVN(path):
  """Returns a boolean indicating whether the git repository is git-svn enabled."""
  fp = open(path + '/.git/config', 'r')
  lines = fp.readlines()
  fp.close()
  for line in lines:
    if line.find('[svn-remote') >= 0:
      return True
  return False

def GetExternals():
  """Returns a list of all the defined svn:externals. Must be called from a git repository."""
  get_externals = subprocess.Popen(["git", "svn", "show-externals"], stdout=subprocess.PIPE)
  get_externals.wait()
  if get_externals.returncode:
    return None
  raw_externals = get_externals.stdout.readlines()
  externals = []
  for ext in raw_externals:
    ext = ext.strip()
    if len(ext) > 0 and ext[0] != '#':
      externals.append(ext.split())
  return externals

def GetSVNRoot():
  """Returns the SVN repository root path. Must be called from a git repository."""
  get_root = subprocess.Popen(["git", "svn", "info"], stdout=subprocess.PIPE)
  get_root.wait()
  if get_root.returncode:
    return None
  info = get_root.stdout.readlines()
  for line in info:
    root_str = 'Root:'
    root_pos = line.find(root_str)
    if root_pos >= 0:
      trimmer = root_pos + len(root_str)
      return line[trimmer:].strip()
  return None

def AddExclude(path, exclude):
  """Adds a path to the .git/info/exclude file."""
  fp = open(path + '/.git/info/exclude', 'r+')
  lines = fp.readlines()
  for line in lines:
    if line.find(exclude) >= 0:
      fp.close()
      return
  fp.write(exclude + "\n")
  fp.close()

def FixupExternals(svn_root, url, path):
    """ Externals from version 1.5 onwards are mis-parsed by git svn show-externals
    Fix them up by spliting around the relative character, and putting the prefix
    onto the start of path.
    e.g. An external in app/app1 of ^/trunk/lib/lib1 at rev 1234 would appear in
    the output as
         /app/app1/^/trunk/lib/lib1@1234 lib1
    this needs to be fixed up as
         <svn_root>/trunk/lib/lib1@1234 app/app1/lib1
    """
    if '^/' in url:
        prefix, url = url.split('^/')
        path = os.path.join(prefix, path)
        path = path.lstrip('/')
        url = svn_root + '/' + url
    return (url, path)

def Main():
  """Main function."""
  parser = optparse.OptionParser()
  parser.add_option("-t", "--type", choices=["svn", "git", "shallow"], default="git", help="Type of checkout to perform for new externals. Choices are svn,git,shallow. git is default.")
  (options, args) = parser.parse_args()

  git_path = GitRepoPath()
  if not git_path:
    print "Please run this script from within a git repository."
    sys.exit(1)
  os.chdir(git_path)

  if not IsGitSVN(git_path):
    print "This git repository was not cloned via git-svn."
    sys.exit(2)

  # Important info for cloning.
  svn_root = GetSVNRoot()
  externals = GetExternals()

  if len(externals) > 0:
    if not os.path.exists(".git_sync"):
      os.mkdir(".git_sync")

  AddExclude(git_path, ".git_sync")

  for ext in externals:
    # Fix up URLs that are relative to SVN repository root.
    url = ext[0]
    path = ext[1]
    url, path = FixupExternals(svn_root, url, path)

    # Split out revision information.
    url_parts = url.split('@')
    url = url_parts[0]
    if len(url_parts) > 1:
      rev = url_parts[1]
      external_pinned = True
    else:
      rev = 'HEAD'
      external_pinned = False
    sync_path = os.path.join(".git_sync", path)

    # Perform the actual checkout.
    if os.path.exists(sync_path):
      # Perform an update on a git repository.
      if os.path.exists(os.path.join(sync_path, ".git")):
        subprocess.Popen(["git", "svn", "rebase"]).wait()
      # Perform an update on a SVN WC.
      elif os.path.exists(os.path.join(sync_path, ".svn")):
        subprocess.Popen(["svn", "update", "-r", rev, sync_path]).wait()
      else:
        print "Unknown repository type at %s" % sync_path
    else:
      # Perform a git checkout.
      if options.type == "git":
        subprocess.Popen(["git", "svn", "clone", url, sync_path]).wait()
      # Perform a SVN checkout.
      elif options.type == "svn":
        subprocess.Popen(["svn", "checkout", "-r", rev, url, sync_path]).wait()
      else:
        print "Cannot clone %s as %s" % (sync_path, options.type)
      # To deal with externals deep in the tree, symlinks need to count the
      # number of path elements they have to go up to get to the head of the tree
      os.symlink(os.path.join('../' * path.count('/'), sync_path),
                 os.path.join(git_path, path))
    AddExclude(git_path, path)

    # If the checkout is a git one, then we need to find the proper SVN revision.
    if os.path.exists(os.path.join(sync_path, ".git")):
      curpath = os.getcwd()
      os.chdir(sync_path)
      if external_pinned:
        get_rev = subprocess.Popen(["git", "svn", "log", "--show-commit", "-r", rev], stdout=subprocess.PIPE)
      else:
        get_rev = subprocess.Popen(["git", "svn", "log", "--show-commit"], stdout=subprocess.PIPE)
      get_rev.wait()
      oneline = get_rev.stdout.readlines()[1].split(' | ')
      subprocess.Popen(["git", "checkout", oneline[1]]).wait()
      os.chdir(curpath)
  # end for

if __name__ == '__main__':
  Main()

