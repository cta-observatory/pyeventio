#!/usr/bin/env python
"""
Usage:
  try_simtelfile.py [-p] <url>

Options:
  -h --help     Show this screen.
  -p     Print the events
"""
import time
from pprint import pprint
from docopt import docopt
from eventio.simtel.simtelfile import SimTelFile

arguments = docopt(__doc__)
source = SimTelFile(arguments['<url>'])

start_time = time.time()
for i, (shower, event) in enumerate(source):
    print('Event id:', i)
    if arguments['-p']:
        pprint(shower)
        pprint(event)
print('  Duration:', time.time() - start_time)
