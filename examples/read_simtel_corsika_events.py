from argparse import ArgumentParser

from eventio import EventIOFile
from eventio.simtel import MCEvent, MCShower

parser = ArgumentParser()
parser.add_argument(
    "inputfile",
    help="Example file: tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz",
)
args = parser.parse_args()

with EventIOFile(args.inputfile) as f:
    for eventio_object in f:
        if isinstance(eventio_object, MCShower):
            shower = eventio_object.parse()
            print('StereoReconstruction: {shower}, Energy={energy:.3f} TeV'.format(**shower))

        if isinstance(eventio_object, MCEvent):
            event = eventio_object.parse()
            event['xcore'] /= 100
            event['ycore'] /= 100

            print(
                "   event_id: {event_id}, core_x={xcore:6.2f} m, core_y={ycore:6.2f} m".format(
                    **event
                )
            )
