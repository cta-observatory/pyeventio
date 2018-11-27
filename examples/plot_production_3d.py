import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pkg_resources import resource_filename
from argparse import ArgumentParser

import eventio

parser = ArgumentParser()
parser.add_argument('-i', '--inputfile', dest='inputfile')
parser.add_argument('-e', '--event', dest='event', type=int, default=0)

args = parser.parse_args()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

testfile = resource_filename('eventio', 'resources/3_gammas_reuse_5.dat')

with eventio.IACTFile(args.inputfile or testfile) as f:
    for i in range(args.event + 1):
        event = next(iter(f))

b = event.photon_bunches[0]

cz = 1 - (b['cx']**2 + b['cy']**2)

obslevel = event.header.observation_levels[0]

x = b['x'] + ((b['zem'] - obslevel) / cz) * b['cx']
y = b['y'] + ((b['zem'] - obslevel) / cz) * b['cy']

ax.scatter(x / 100, y / 100, b['zem'] / 1e5, s=3, lw=0, c='k')
ax.set_xlabel('x / m')
ax.set_ylabel('y / m')
ax.set_zlabel('z / km')
plt.show()
