import matplotlib.pyplot as plt
from eventio import IACTFile
import numpy as np
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-o', '--output-file')
parser.add_argument('-b', '--n-bins', default=500, type=int)
parser.add_argument('-e', '--event', default=1)

masses = {
    'Electrons': 0.000511,
    'Muons': 0.105658,
    'Pions': 0.139570,
}


def main():
    args = parser.parse_args()
    f = IACTFile(args.inputfile)
    it = iter(f)

    radius = f.telescope_positions['r'][0] / 100

    for i in range(args.event):
        event = next(it)

    photons = event.photon_bunches[0]
    emitter = event.emitter[0]

    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    image = np.zeros((args.n_bins, args.n_bins, 3))

    ax.set_title('R: Electrons, G: Muons, B: Pions')

    for i, (particle, mass) in enumerate(masses.items()):
        mask = np.isclose(emitter['mass'], mass, rtol=1e-4)

        hist, edges, edges = np.histogram2d(
            photons['x'][mask] / 100,
            photons['y'][mask] / 100,
            bins=args.n_bins,
            range=[[-radius, radius], [-radius, radius]],
        )
        hist = np.log10(1 + hist)
        image[:, :, i] = hist.T[::-1, :]

    image /= image.max()
    plt.imshow(image, extent=[-radius, radius, -radius, radius])
    plt.xlabel('x / m')
    plt.ylabel('y / m')
    plt.tight_layout()

    if args.output_file is None:
        plt.show()
    else:
        plt.savefig(args.output_file)


if __name__ == '__main__':
    main()
