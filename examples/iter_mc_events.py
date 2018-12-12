import time
from eventio.simtel.simtelfile import SimTelFile
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np

parser = ArgumentParser()
parser.add_argument('inputfile')

args = parser.parse_args()

start_time = time.time()

energies = []
corex = []
corey = []
with SimTelFile(args.inputfile) as f:
    for i, event in enumerate(f.iter_mc_events()):
        energies.append(event['mc_shower']['energy'])
        corex.append(event['mc_event']['xcore'])
        corey.append(event['mc_event']['ycore'])

print('  Duration:', time.time() - start_time)


bins = np.logspace(
    np.log10(np.min(energies)),
    np.log10(np.max(energies)),
    51
)

plt.figure()
plt.hist(energies, bins=bins)
plt.xscale('log')
plt.xlabel(r'$E \,/\, \mathrm{TeV}$')
plt.tight_layout()


fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.hist2d(
    corex, corey,
    bins=100
)

fig.tight_layout()
plt.show()
