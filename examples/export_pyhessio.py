'''Export simtel data to hdf5 using pyhessio'''
import pyhessio
import pandas as pd
from argparse import ArgumentParser


parser = ArgumentParser(__doc__)
parser.add_argument('inputfile')
parser.add_argument('outputfile')
args = parser.parse_args()


def write_instrument_info(f, hdf):
    tels = f.get_telescope_ids()
    print(tels)


with pd.HDFStore(args.outputfile, 'w') as hdf:
    with pyhessio.open_hessio(args.inputfile) as f:
        for i, event in enumerate(f.move_to_next_event()):

            if i == 0:
                write_instrument_info(f, hdf)
