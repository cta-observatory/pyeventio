# coding: utf-8
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
from eventio import IACTFile
from matplotlib.colors import ListedColormap
import numpy as np
from itertools import zip_longest
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-b', '--n-bins', type=int, default=500)
parser.add_argument('-o', '--output')
parser.add_argument('-e', '--event', default=1)

masses = {
    'Electrons': 0.000511,
    'Muons': 0.105658,
    'Pions': 0.139570,
    'Kaons': 0.493677,
    'Protons': 0.938272,
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

    fig, axs2d = plt.subplots(2, 3, figsize=(19.2, 10.8))
    axs = [ax for axs in axs2d for ax in axs]

    for ax, (particle, mass) in zip_longest(axs[:-1], masses.items()):

        mask = np.isclose(emitter['mass'], mass)

        ax.set_facecolor('k')
        ax.set_aspect(1)
        ax.set_title(particle)
        ax.set_ylim(-radius, radius)
        ax.set_xlim(-radius, radius)
        ax.set_xlabel('x / m')
        ax.set_xlabel('y / m')

        if mask.sum() > 0:
            hist, edges, edges, img = ax.hist2d(
                photons['x'][mask] / 100,
                photons['y'][mask] / 100,
                cmap='gray',
                bins=args.n_bins,
                range=[[-radius, radius], [-radius, radius]],
                norm=LogNorm(),
            )
        else:
            img = ax.imshow(
                np.zeros((args.n_bins, args.n_bins)),
                cmap='gray',
                extent=[-radius, radius, -radius, radius],
                vmin=0, vmax=1,
            )
        fig.colorbar(img, ax=ax)

    particle_id = event.particles['particle_id'] // 1000
    particle_ids = {
        1: 'γ',
        2: 'e⁺',
        3: 'e⁻',
        5: 'μ⁺',
        6: 'μ⁻',
        13: 'n',
        14: 'p',
        15: r'$\bar{p}$',
    }

    cmap = ListedColormap([f'C{i}' for i in range(len(particle_ids))])

    for i, pid in enumerate(particle_ids.keys()):
        particle_id[particle_id == pid] = i

    scat = axs[-1].scatter(
        event.particles['x'] / 100,
        event.particles['y'] / 100,
        c=particle_id,
        zorder=10,
        cmap=cmap,
        vmin=-0.5, vmax=len(particle_ids) - 0.5,
    )
    axs[-1].set_title('Particles reacing obslevel')
    axs[-1].set_xlim(-radius, radius)
    axs[-1].set_ylim(-radius, radius)
    bar = fig.colorbar(scat, ax=axs[5])
    bar.set_ticks(np.arange(len(particle_ids)))
    bar.set_ticklabels(list(particle_ids.values()))
    bar.update_bruteforce(scat)

    fig.tight_layout()
    if args.output:
        fig.savefig(args.output, dpi=200)
    else:
        plt.show()


if __name__ == '__main__':
    main()
