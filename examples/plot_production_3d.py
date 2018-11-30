import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pkg_resources import resource_filename
from argparse import ArgumentParser

import eventio

parser = ArgumentParser()
parser.add_argument('-i', '--inputfile', dest='inputfile')
parser.add_argument('-e', '--event', dest='event', type=int, default=0)

args = parser.parse_args()


testfile = resource_filename('eventio', 'resources/3_gammas_reuse_5.dat')

with eventio.IACTFile(args.inputfile or testfile) as f:
    it = iter(f)
    event = next(it)
    for i in range(args.event):
        event = next(it)

    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1], projection='3d')

    obslevel = event.header.observation_levels[0]

    for pos, b in zip(f.telescope_positions, event.photon_bunches.values()):
        cz = 1 - (b['cx']**2 + b['cy']**2)
        x = b['x'] + ((b['zem'] - obslevel) / cz) * b['cx']
        y = b['y'] + ((b['zem'] - obslevel) / cz) * b['cy']

        x -= pos[0]
        y -= pos[1]

        ax.scatter(x / 100, y / 100, b['zem'] / 1e5, s=3, lw=0, c='k', alpha=0.2)

    ax.view_init(10, 45)
    ax.set_xlabel('x / m')
    ax.set_ylabel('y / m')
    ax.set_zlabel('z / km')
    fig.savefig('shower.png', dpi=300)
