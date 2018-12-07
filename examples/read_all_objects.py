from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first

path = 'eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'

with EventIOFile(path) as f:
    for o, level in yield_all_objects_depth_first(f):
        if hasattr(o, 'parse'):
            o.parse()
