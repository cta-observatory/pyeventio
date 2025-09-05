import time
from eventio.simtel.simtelfile import SimTelFile
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np

parser = ArgumentParser()
parser.add_argument(
    "inputfile", help="Example file: tests/resources/40k_pixels.simtel.zst"
)

args = parser.parse_args()

start_time = time.time()

energies = []
corex = []
corey = []

# to get all simulated mc events, we set skip_non_triggered to False
with SimTelFile(args.inputfile, skip_non_triggered=False) as f:
    for i, event in enumerate(f):
        energies.append(event['mc_shower']['energy'])
        corex.append(event['mc_event']['xcore'])
        corey.append(event['mc_event']['ycore'])

print('  Duration:', time.time() - start_time)


bins = np.logspace(
    np.log10(np.min(energies)),
    np.log10(np.max(energies)),
    51
)

fig, (ax1, ax2) = plt.subplots(1, 2, layout="constrained")

ax1.hist(energies, bins=bins)
ax1.set(
    xscale='log',
    yscale='log',
    xlabel=r'$E \,/\, \mathrm{TeV}$',
)


ax2.hist2d(
    corex, corey,
    bins=100
)
ax2.set(
    aspect=1,
    xlabel=r'$x \,/\, \mathrm{m}$',
    ylabel=r'$y \,/\, \mathrm{m}$',
)

plt.show()
