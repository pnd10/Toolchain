#!/usr/bin/env python

"""Command Line Speed Test

This script will perform a speed test and will append the results to a CSV
file. You can use this script as a cron job to regularly test your bandwidth.

I recommend using this cron format to run it every 17 hours (which will test
at different times every day):
0 */17 * * * /path/to/speed-test.py
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
import urllib

"""File to append results to in CSV format."""
RESULT_DATA_FILE = os.path.expanduser("~/speed-test-results.txt")

"""The file to try to download, used for testing speed."""
SPEED_TEST_FILE = "http://ubuntu.media.mit.edu/ubuntu-releases/jaunty/ubuntu-9.04-desktop-i386.iso"

"""The number of recent data trys that should be included in the chart."""
CHART_CARDINALITY = 50

"""Location to store the chart."""
CHART_FILE = os.path.expanduser("~/speed-test-chart.png")

###################################################################

def _ConvertSpeed(speed):
  """Converts a human-readable speed string (e.g. 2.4 MB/s) into KB/s float values."""
  unit = speed[len(speed)-4:]
  rate = speed[0:len(speed)-5]
  if unit == "MB/s":
    return str(float(rate)*1024)
  elif unit == "KB/s":
    return rate
  else:
    raise Exception("Unknown unit %s" % unit)

def RunSpeedTest(work_dir):
  """Downloads the test file and return the results."""
  
  # Start the timer.
  start_time = time.time()
  
  # Run the speed test.
  proc = subprocess.Popen("wget -v -o %s -O output.bin '%s'" % (work_dir+'/log.txt', SPEED_TEST_FILE), shell=True, cwd=work_dir)
  proc.wait()
  
  # Stop timer.
  end_time = time.time()
  
  # Get wget reporting information.
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

def CreateChart(tuples):
  """Creates a chart for the most recent reporting data."""
  # Indexes in the tuple for the columns we care about.
  idx_date_ = 0
  idx_speed_ = 2
  
  tuples_len = len(tuples)
  if tuples_len > CHART_CARDINALITY:
    tuples = tuples[tuples_len-CHART_CARDINALITY : tuples_len]
    tuples_len = CHART_CARDINALITY
  height = 300
  width = (10 * CHART_CARDINALITY) + 20 # Two pixels per every data point for good spacing.
  # if width > 1000: # Google enforces a max width.
  width = 1000
  
  # De-CSV the tuples.
  tuples_split = map(lambda t: t.split(','), tuples)
  
  data_points = map(lambda t: _ConvertSpeed(t[idx_speed_]), tuples_split)
  data_points_floats = map(lambda f: float(f), data_points)
  
  min_val = min(data_points_floats)
  max_val = max(data_points_floats)
  
  x_values = list()
  i = 0
  for tup in tuples_split:
    if i % 5 == 0:
      x_values += [datetime.fromtimestamp(float(tup[idx_date_])).strftime("%d/%m %H:%m")]
    i += 1
  
  chart_url = "http://chart.apis.google.com/chart?chtt=%s&cht=lc&chg=2,20&chm=o,0066FF,0,-1.0,6&chs=%dx%d&chd=t:%s&chds=%f,%f&chxt=x,y&chxl=0:|%s|1:|%s|" % (
    urllib.quote("Speed Test Results (KB/s) by Date"),
    width, height,
    ','.join(data_points),
    min_val-100, max_val+100, # Fuzz the min and max for spacing issues.
    '|'.join(map(urllib.quote, x_values)),
    '|'.join((str(min_val-100), str(min_val), str((min_val+max_val)/2), str(max_val), str(max_val+100))),
  )
  return chart_url

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
  
  # Create the chart.
  results_.seek(0)
  tuples = results_.readlines()
  chart_url = CreateChart(tuples[1:])
  urllib.urlretrieve(chart_url, CHART_FILE)
  
  # Clean the work directory.
  shutil.rmtree(output_dir, True)

if __name__ == '__main__':
  sys.exit(Main())
