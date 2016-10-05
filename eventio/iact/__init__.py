import warnings
import logging
import numpy as np
from collections import namedtuple
from ..exceptions import WrongTypeException
log = logging.getLogger(__name__)
from .objects import parse_eventio_object
from ..event_io_file import objects

def sort_objects_into_showers(objects):
    '''
    The objects in IACT run files build up showers 
    when looking at the object.headers[-1].type of a list of objects
    (where the first 3 and the last 1 object was stripped off already)
    we find a shower looks like this: 
    [...
     1202,
     1203,
     1205,
     ...
     1205,
     1209,
     ...
    ]
    '''
    showers = []
    while True:
        try:
            idx = [o.headers[-1].type for o in objects].index(1209) + 1
        except:
            break
        new_shower, objects = objects[:idx], objects[idx:]
        showers.append(new_shower)
    return showers


def generate_event(shower):
    '''
    A shower is simply a list of EventIOObject
    of these kinds:
        - CorsikaEventHeader(exactly 1)
        - CorsikaArrayOffsets(exaclty 1)
        - IACTPhotons(more than one or even zero)
        - CorsikaEventEndBlock(exactly 1)
    '''
    header = parse_eventio_object(shower[0])
    array_offsets = parse_eventio_object(shower[1])
    end_block = parse_eventio_object(shower[-1])

    for reuse_id, reuse_event in enumerate(shower[2:-1]):
        photon_bunches = parse_eventio_object(reuse_event)

        yield CorsikaEvent(
            header=header,
            end_block=end_block,
            photon_bunches=photon_bunches,
            time_offset=array_offsets.time_offset,
            x_offset=array_offsets.offsets['x'],
            y_offset=array_offsets.offsets['y'],
            weight=array_offsets.offsets['weight'],
            shower=shower[0].headers[0].id,
            reuse=reuse_id,
        )

CorsikaEvent = namedtuple(
    'CorsikaEvent',
    [
        'header', 'end_block', 'photon_bunches',
        'time_offset', 'x_offset', 'y_offset', 'weight',
        'shower', 'reuse',
    ]
)



class IACTFile:
    '''
    An Interface to access the data of a EventIO file
    as produced by the CORSIKA IACT (a.k.a. bernlohr) extension
    more easily.

    Instead of low-level access to eventio items, it provides
    direct access to telescope events and simulation settings.

    For example, it iterates over CorsikaEvent instances and
    IACTFile[n] will return the nth event in the file.

    The structure of an IACT EventIO file is assumed to be like this:

    CorsikaRunHeader
    CorsikaInputCard
    CorsikaTelescopeDefinition

    For each Event:
      CorsikaEventHeader
      CorsikaArrayOffsets
      For each reuse:
        CorsikaTelescopeData
        For each Telescope:
          IACTPhotons
      CorsikaEventEndBlock

    CorsikaRunEndBlock
    '''

    def __init__(self, path):
        self.objects = objects(path)
        self.run_header = parse_eventio_object(self.objects[0])
        self.input_card= parse_eventio_object(self.objects[1])
        self.telescope_definition = parse_eventio_object(self.objects[2])
        self.end_block = parse_eventio_object(self.objects[-1])
        self.n_telescopes = self.telescope_definition.n_telescopes
        self.telescope_positions = self.telescope_definition.tel_pos
        self.showers = sort_objects_into_showers(self.objects[3:-1])

        self._iter = None
    def __iter__(self):
        for shower in self.showers:
            for event in generate_event(shower):
                yield event

    def __next__(self):
        if not self._iter:
            self._iter = iter(self)
        return next(self._iter)

