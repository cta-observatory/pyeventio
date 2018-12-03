from eventio import EventIOFile, Histograms
import matplotlib.pyplot as plt
from eventio.search_utils import find_type
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
    o = find_type(f, Histograms)
    hists = o.parse_data_field()

    for hist in hists:
        plt.figure()
        x_bins = np.linspace(hist['lower_x'], hist['upper_x'], hist['n_bins_x'] + 1)

        if hist['n_bins_y'] > 0:
            y_bins = np.linspace(hist['lower_y'], hist['upper_y'], hist['n_bins_y'] + 1)

            plt.pcolormesh(x_bins, y_bins, hists[0]['data'].T)

        else:
            centers = 0.5 * (x_bins[:-1] + x_bins[1:])
            plt.hist(centers, bins=x_bins, weights=hist['data'])

        plt.title(hist['title'])
        plt.tight_layout()

plt.show()
