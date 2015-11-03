#!/usr/bin/python
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import os
import sys

plt.ion()

filename = sys.argv[1]
csv_file = open(filename)
photons = np.loadtxt(filter(lambda row: row[0]!='#', csv_file))
csv_file.close()

photon_indices = np.random.choice(np.arange(len(photons)), len(photons)/10, replace=False)
print photon_indices
photons = photons[photon_indices]

fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_xlabel('x[m]')
ax.set_ylabel('y[m]')
ax.set_zlabel('z[m]')
c0 = 299792458.0

# shifting relative arrival times
photons[:,4] -= photons[:,4].min()



backtrace_time = 66e-6

support = np.zeros((3, len(photons)))
support[0] =  photons[:,0]
support[1] =  photons[:,1]

direction = np.zeros((3, len(photons)))
direction[0] = photons[:,2]
direction[1] = photons[:,3]
direction[2] = np.sqrt(1 - direction[0]**2 - direction[1]**2)

relative_arrival_time = photons[:,4]
production = support + direction*c0*(relative_arrival_time + backtrace_time)

px = production[0]
py = production[1]
pz = production[2]
ax.scatter(px, py, pz, c='b', marker='o')

    

for i,photon in enumerate(photons):
    
    x = [support[0, i],production[0, i]]
    y = [support[1, i],production[1, i]]
    z = [support[2, i],production[2, i]]

    ax.plot(x, y, z)

    

