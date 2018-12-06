import time
from pprint import pprint
from eventio.simtel.simtelfile import SimTelFile
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-p', '--print', action='store_true')

args = parser.parse_args()

source = SimTelFile(args.inputfile)

start_time = time.time()
for i, (shower, event) in enumerate(source):
    print('Event id:', i)
    if args.print:
        pprint(shower)
        pprint(event)

print('  Duration:', time.time() - start_time)
