import cProfile
import pstats
from io import StringIO
from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('inputfile')
parser.add_argument('-s', '--sort', default='cumtime')
parser.add_argument('-l', '--limit', default=50, type=int)
args = parser.parse_args()

pr = cProfile.Profile()
pr.enable()

with EventIOFile(args.inputfile) as f:
    for o, level in yield_all_objects_depth_first(f):
        if hasattr(o, 'parse'):
            o.parse()

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats(args.sort)

ps.print_stats(args.limit)
print(s.getvalue())
