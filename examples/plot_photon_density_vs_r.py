import matplotlib.pyplot as plt
from argparse import ArgumentParser
import numpy as np
import pandas as pd
from matplotlib.colors import hsv_to_rgb

from eventio import IACTFile

parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-e', '--event', type=int, default=0)
parser.add_argument('-t', '--telescope', type=int)
parser.add_argument('-n', '--n-bins', type=int, default=500)
parser.add_argument('-r', '--radius', type=float)
parser.add_argument('-o', '--outputfile')


def percentile(p):
    def perc(data):
        return np.percentile(data, p)
    perc.__name__ = f'{p}%'
    return perc


def main():
    args = parser.parse_args()

    with IACTFile(args.inputfile) as f:
        it = iter(f)
        event = next(it)
        for i in range(args.event):
            event = next(it)

        if args.telescope:
            photons = [event.photon_bunches[args.telescope]]
            positions = [f.telescope_positions[args.telescope]]
        else:
            photons = list(event.photon_bunches.values())
            positions = f.telescope_positions

        if args.radius is None:
            args.radius = f.telescope_positions['r'][0] / 100

        edges = np.linspace(-args.radius, args.radius, args.n_bins + 1)

        hists = []
        for pos, tel_photons in zip(positions, photons):
            hist, _, _ = np.histogram2d(
                (tel_photons['x'] + pos[0]) / 100,
                (tel_photons['y'] + pos[1]) / 100,
                edges,
            )
            hists.append(hist)
        img = np.sum(hists, axis=0)

        center = 0.5 * (edges[:-1] + edges[1:])
        width = np.diff(edges)[0]
        y, x = np.meshgrid(center, center)
        r = np.sqrt(x**2 + y**2)

        df = pd.DataFrame({
            'r': r.ravel(),
            'x': x.ravel(),
            'y': y.ravel(),
            'density': img.ravel() / width**2
        })

        n_bins = 100
        r = np.linspace(0, args.radius * np.sqrt(2), n_bins + 1)
        df['bin'] = np.digitize(df['r'], r)
        width = np.diff(r)

        binned = pd.DataFrame({
            'r_min': r[:-1],
            'r_max': r[1:],
            'r_center': 0.5 * (r[:-1] + r[1:]),
            'r_width': np.diff(r),
        }, index=np.arange(1, n_bins + 1))

        binned = binned.join(df.groupby('bin')['density'].agg(
            ['median', percentile(5), percentile(16), percentile(84), percentile(95)]
        ))

        fig, ax = plt.subplots()

        x = np.zeros(n_bins * 2)
        x[0::2] = binned['r_min']
        x[1::2] = binned['r_max']

        ax.errorbar(binned.r_center, binned['median'], xerr=binned.r_width / 2, ls='', label='Median')

        y_low = np.repeat(binned['16%'], 2)
        y_high = np.repeat(binned['84%'], 2)
        ax.fill_between(x, y_low, y_high, color=hsv_to_rgb((0.6, 0.32, 1.0)), label='68% containment', zorder=0)

        y_low = np.repeat(binned['5%'], 2)
        y_high = np.repeat(binned['95%'], 2)
        ax.fill_between(x, y_low, y_high, color=hsv_to_rgb((0.6, 0.1, 1.0)), label='90% containment', zorder=-1)

        ax.margins(0, 0)


        ax.set_ylabel('Photons / m²')
        ax.set_xlabel('Core distance / m')
        ax.legend()

        fig.tight_layout()

        if args.outputfile:
            fig.savefig(args.outputfile, dpi=300)
        else:
            plt.show()


if __name__ == '__main__':
    main()

