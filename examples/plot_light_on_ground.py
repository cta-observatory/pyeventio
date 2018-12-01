import matplotlib.pyplot as plt
from pkg_resources import resource_filename
from argparse import ArgumentParser

from eventio import IACTFile

parser = ArgumentParser()
parser.add_argument('-i', '--inputfile', dest='inputfile')
parser.add_argument('-e', '--event', dest='event', type=int, default=0)
parser.add_argument('-t', '--telescope', dest='telescope', type=int)


def main():
    args = parser.parse_args()
    if not args.inputfile:
        args.inputfile = resource_filename('eventio', 'resources/one_shower.dat')

    with IACTFile(args.inputfile) as f:

        for event in f:
            if args.telescope:
                photons = [event.photon_bunches[args.telescope]]
                positions = [f.telescope_positions[args.telescope]]
            else:
                photons = list(event.photon_bunches.values())
                positions = f.telescope_positions

            fig, ax = plt.subplots()
            ax.set_aspect(1)
            ax.set_facecolor('k')

            for pos, tel_photons in zip(positions, photons):
                ax.scatter(
                    x=tel_photons['x'] + pos[0],
                    y=tel_photons['y'] + pos[1],
                    c='w',
                    s=10,
                    lw=0,
                )

            plt.show()


if __name__ == '__main__':
    main()
