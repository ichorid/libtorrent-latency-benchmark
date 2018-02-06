#!/usr/bin/env python3
# createPlot.py

"""
This script plots data in a csv into a graph with labels.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

# Give the file name, test duration, latency interval size and filename to save under.
numVars = 4
if len(sys.argv) != numVars + 1:
    print("Give me", numVars, "arguments!")

# Get the given arguments
fileName = sys.argv[1]
testDuration = int(sys.argv[2])
latencyIntervals = int(sys.argv[3])

# Read download speeds from the file
data = np.genfromtxt(fileName, delimiter=',')
data = data.transpose()
delays = [latencyIntervals * step for step in range(len(data))]
lines = plt.plot(np.linspace(0, testDuration, len(data)), data)

for index, line in enumerate(lines):
    line.set_label('#' + str(index) + ' ' + str(delays[index]) + "ms")

plt.ylabel("Download speed [kB / s]")
plt.xlabel("Time [s]")

plt.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

plt.legend()
plt.savefig(sys.argv[4])
