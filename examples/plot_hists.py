from eventio import EventIOFile, Histograms
import matplotlib.pyplot as plt
from eventio.search_utils import collect_toplevel_of_type
import numpy as np
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument(
    'inputfile',
    nargs='*'
)
default = 'eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'

args = parser.parse_args()
inputfile = args.inputfile[0] or default

with EventIOFile(inputfile) as f:
    for o in  collect_toplevel_of_type(f, Histograms):
        hists = o.parse_data_field()

        for hist in hists:
            plt.figure()

            x_bins = np.linspace(
                hist['lower_x'],
                hist['upper_x'],
                hist['n_bins_x'] + 1
            )

            if hist['n_bins_y'] > 0:
                y_bins = np.linspace(
                    hist['lower_y'],
                    hist['upper_y'],
                    hist['n_bins_y'] + 1
                )

                plt.pcolormesh(x_bins, y_bins, hist['data'])

                marginal_x = np.sum(hist['data'], axis=0)
                marginal_y = np.sum(hist['data'], axis=1)

                non_zero_x, = np.where(marginal_x != 0)
                plt.xlim(x_bins[non_zero_x[0]], x_bins[non_zero_x[-1] + 1])

                non_zero_y, = np.where(marginal_y != 0)
                plt.ylim(y_bins[non_zero_y[0]], y_bins[non_zero_y[-1] + 1])

            else:
                centers = 0.5 * (x_bins[:-1] + x_bins[1:])
                plt.hist(centers, bins=x_bins, weights=hist['data'])

                non_zero_x, = np.where(hist['data'] != 0)
                plt.xlim(x_bins[non_zero_x[0]], x_bins[non_zero_x[-1] + 1])

            plt.title(hist['title'])
            plt.tight_layout()

plt.show()
