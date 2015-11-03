import sys
import eventio
import glob
import time
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import os

plt.ion()
fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_xlabel('x[m]')
ax.set_ylabel('y[m]')
ax.set_zlabel('z[m]')
c0 = 3e8 #299792458.0

filename = sys.argv[1] if len(sys.argv)>1 else 'data/telescope.dat'
#f = eventio.EventIoFile(filename, debug=False)

f = eventio.EventIoFileStream(filename, debug=False)
p = f.next()

b = p.bunches

random_indices = np.random.choice(np.arange(len(b)), 10000, replace=False)
photons = b[random_indices]
#photons = b

# shifting relative arrival times
photons['time'] -= photons['time'].min()



#backtrace_time = 66e-6

support = np.zeros((3, len(photons)))
support[0] =  photons['x']
support[1] =  photons['y']

direction = np.zeros((3, len(photons)))
direction[0] = photons['cx']
direction[1] = photons['cy']
direction[2] = np.sqrt(1 - direction[0]**2 - direction[1]**2)

relative_arrival_time = photons['time']
production = support + direction*(photons['zem']/direction[2])

production /=100.
support /= 100.

px = production[0]
py = production[1]
pz = production[2]
ax.scatter(px, py, pz, c='b', marker=',')


ax.set_xlim(-15000, 15000)
ax.set_ylim(-15000, 15000)
ax.set_zlim(0., 30000)

"""
for i,photon in enumerate(photons):
	break    
    x = [support[0, i],production[0, i]]
    y = [support[1, i],production[1, i]]
    z = [support[2, i],production[2, i]]

    ax.plot(x, y, z)

    

"""