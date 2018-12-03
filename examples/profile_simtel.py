import cProfile
import pstats
from io import StringIO
from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first

path = 'eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'

pr = cProfile.Profile()
pr.enable()

with EventIOFile(path) as f:
    for o, level in yield_all_objects_depth_first(f):
        if hasattr(o, 'parse_data_field'):
            o.parse_data_field()

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')

ps.print_stats()
print(s.getvalue())
