from argparse import ArgumentParser

from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first
import textwrap

parser = ArgumentParser()
parser.add_argument(
    "inputfile",
    help="Example file: tests/resource/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz",
)
args = parser.parse_args()

with EventIOFile(args.inputfile) as f:
    for o, level in yield_all_objects_depth_first(f):
        if hasattr(o, 'parse') and not o.header.only_subobjects:
            print(repr(o), "\n", textwrap.indent(str(o.parse()), "    "))
