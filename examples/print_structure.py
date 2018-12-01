from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first

with EventIOFile('eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz') as f:
    for o, level in yield_all_objects_depth_first(f):
        print('    ' * level, o)
