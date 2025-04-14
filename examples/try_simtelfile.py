import time
from pprint import pprint
from eventio.simtel.simtelfile import SimTelFile
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument(
    "inputfile",
    help="tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz",
)
parser.add_argument('-p', '--print', action='store_true')

args = parser.parse_args()

start_time = time.time()

with SimTelFile(args.inputfile) as f:
    for i, event in enumerate(f):
        print('Event count: {: 04d}, E = {:8.3f} Tev, #Telescopes={: 3d}'.format(
            i, event['mc_shower']['energy'], len(event['telescope_events'])
        ))
        if args.print:
            pprint(event)

print('  Duration:', time.time() - start_time)
