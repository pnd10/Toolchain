#!/usr/bin/env python

"""Command Line Speed Test

This script will perform a speed test and will append the results to a CSV
file. You can use this script as a cron job to regularly test your bandwidth.
"""

from datetime import datetime
import os
import os.path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import tempfile

"""File to append results to in CSV format."""
RESULT_DATA_FILE = os.path.expanduser("~/speed-test-results.txt")

"""The file to try to download, used for testing speed."""
SPEED_TEST_FILE = "http://ubuntu.media.mit.edu/ubuntu-releases/jaunty/ubuntu-9.04-desktop-i386.iso"

###################################################################

def RunSpeedTest(work_dir):
  """Downloads the test file and return the results."""
  
  # Start the timer.
  start_time = time.time()
  
  # Run the speed test.
  proc = subprocess.Popen("wget -v -o %s -O output.bin '%s'" % (work_dir+'/log.txt', SPEED_TEST_FILE), shell=True, cwd=work_dir)
  proc.wait()
  
  # Stop timer.
  end_time = time.time()
  
  # Get WGET reporting information.
  logfile = open(work_dir + '/log.txt', 'r')
  wget_output = logfile.readlines()
  logfile.close()
  
  # Go backwards through the wget log to find the transfer summary line.
  wget_speed = None
  for line in reversed(wget_output):
    # First non-empty line is the summary.
    if line.strip() != "":
      wget_speed = re.findall(r'\(([0-9\.]+ [A-Za-z]{2,}/s)\)', line)
      break
  
  # Calculate Python reporting information.
  fsize = os.path.getsize(work_dir + '/output.bin')
  time_delta = end_time - start_time
  py_speed = fsize / time_delta
  py_speed /= 1024
  
  # Return the result tuple.
  return (int(start_time), datetime.fromtimestamp(start_time).isoformat(), wget_speed[0], "%.3f KB/s"%py_speed, time_delta, fsize)

def UpdateLogFile(results, results_):
  """Updates the results file with the given results tuple."""
  for r in results:
    if str(r).find(',') == -1:
      results_.write("%s," % r)
    else:
      results_.write('"%s",' % r)
  results_.write("\n")

def Main():
  """Main program body. Runs a speed test and stores the result."""
  output_dir = tempfile.mkdtemp()
  
  # If this is creating our logfile, put in the CSV header.
  do_setup = False
  if not os.path.exists(RESULT_DATA_FILE):
    do_setup = True
  results_ = open(RESULT_DATA_FILE, 'a')
  if do_setup:
    results_.write("timestamp,date,wget_speed,py_speed,time,fsize\n")
  
  results = RunSpeedTest(output_dir)
  UpdateLogFile(results, results_)
  
  # Clean the work directory.
  shutil.rmtree(output_dir, True)

if __name__ == '__main__':
  sys.exit(Main())
