import matplotlib.pyplot as plt
from pkg_resources import resource_filename
from argparse import ArgumentParser

from eventio import IACTFile

parser = ArgumentParser()
parser.add_argument('-i', '--inputfile', dest='inputfile')
parser.add_argument('-e', '--event', dest='event', type=int, default=0)


def main():
    args = parser.parse_args()
    if not args.inputfile:
        args.inputfile = resource_filename('eventio', 'resources/one_shower.dat')

    with IACTFile(args.inputfile) as f:

        event = f[args.event]
        photons = event.photon_bunches[0]

        fig, ax = plt.subplots()
        ax.set_aspect(1)
        ax.set_axis_bgcolor('k')

        ax.scatter(
            x=photons['x'],
            y=photons['y'],
            c='w',
            s=5,
            alpha=0.1,
            lw=0,
        )

        plt.show()

if __name__ == '__main__':
    main()
