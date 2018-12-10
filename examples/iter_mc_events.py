import time
from pprint import pprint
from eventio.simtel.simtelfile import SimTelFile
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('inputfile')

args = parser.parse_args()

start_time = time.time()

with SimTelFile(args.inputfile) as f:
    for i, event in enumerate(f.iter_mc_events()):
        print('Event {: 8d}, E = {:8.3f} Tev, xcore={:-5.0f} m, ycore={:=5.0f} m'.format(
            event['event_id'],
            event['mc_shower']['energy'],
            event['mc_event']['xcore'],
            event['mc_event']['ycore']
        ))

print('  Duration:', time.time() - start_time)
