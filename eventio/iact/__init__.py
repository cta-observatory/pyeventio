import warnings
import logging
import numpy as np
from collections import namedtuple

from ..base import known_objects, EventIOFile
from ..exceptions import WrongTypeException
from .objects import (
    CorsikaRunHeader,
    CorsikaTelescopeDefinition,
    CorsikaEventHeader,
    CorsikaArrayOffsets,
    CorsikaTelescopeData,
    IACTPhotons,
    IACTLayout,
    IACTTriggerTime,
    IACTPhotoElectrons,
    CorsikaEventEndBlock,
    CorsikaRunEndBlock,
    CorsikaLongitudinal,
    CorsikaInputCard,
)


known_objects.update({
    o.eventio_type: o
    for o in [
        CorsikaRunHeader,
        CorsikaTelescopeDefinition,
        CorsikaEventHeader,
        CorsikaArrayOffsets,
        CorsikaTelescopeData,
        IACTPhotons,
        IACTLayout,
        IACTTriggerTime,
        IACTPhotoElectrons,
        CorsikaEventEndBlock,
        CorsikaRunEndBlock,
        CorsikaLongitudinal,
        CorsikaInputCard,
    ]
})

log = logging.getLogger(__name__)


class IACTFile(EventIOFile):
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
        super().__init__(path)

        if not isinstance(self.objects[0], CorsikaRunHeader):
            raise WrongTypeException('Object 0 is not a CORSIKA run header')
        self.header = self.objects[0].parse_data_field()

        if not isinstance(self.objects[1], CorsikaInputCard):
            raise WrongTypeException('Object 1 is not a CORSIKA input card')
        self.input_card = self.objects[1].parse_data_field()

        if not isinstance(self.objects[2], CorsikaTelescopeDefinition):
            raise WrongTypeException('Object 2 is not a CORSIKA telescope definition')
        self.n_telescopes = self.objects[2].n_telescopes
        self.telescope_positions = self.objects[2].parse_data_field()

        self._parse_events()

        if not isinstance(self.objects[-1], CorsikaRunEndBlock):
            warnings.warn(
                'Last Object is not a CORSIKA Run End Block.'
                'The file seems to be truncated.'
            )
        else:
            self.end_block = self.objects[-1].parse_data_field()

    def __repr__(self):
        return (
            '{}(\n'
            '  path={}\n'
            '  n_telescopes={}\n'
            '  n_events={}\n'
            ')'
        ).format(
            self.__class__.__name__,
            self.path,
            self.n_telescopes,
            self.n_events,
        )

    def __len__(self):
        return self.n_events

    def __iter__(self):
        for event_num in range(self.n_events):
            yield self[event_num]

    def __getitem__(self, idx):
        if idx < 0:
            idx = self.n_events - idx
        if idx >= self.n_events:
            raise ValueError(
                'Index {} is out of range for {} with {} Events'.format(
                    idx, self.__class__.__name__, self.n_events,
                ))
        return self._build_event(idx)

    def _parse_events(self):
        ''' Sort the objects of this file according to the showers they belong to '''
        self._shower_objects = []
        reuse_values = []

        for obj in self.objects:
            if isinstance(obj, CorsikaRunEndBlock):
                break

            if isinstance(obj, CorsikaEventHeader):
                self._shower_objects.append({})
                self._shower_objects[-1]['header'] = obj

            elif isinstance(obj, CorsikaEventEndBlock):
                self._shower_objects[-1]['end_block'] = obj

            elif isinstance(obj, CorsikaArrayOffsets):
                reuse_values.append(obj.n_reuses)
                self._shower_objects[-1]['array_offsets'] = obj

            elif isinstance(obj, CorsikaTelescopeData):
                if 'telescope_data' not in self._shower_objects[-1]:
                    self._shower_objects[-1]['telescope_data'] = []
                self._shower_objects[-1]['telescope_data'].append(obj)

        self.n_showers = len(self._shower_objects)

        if reuse_values:
            assert len(reuse_values) == self.n_showers
            self.reuse = True
            self.n_events = sum(reuse_values)
            self.first_event_in_shower = np.cumsum(reuse_values) - np.array(reuse_values)
        else:
            self.reuse = False
            self.n_events = len(self._shower_objects)

    def _build_event(self, event_num):
        if self.reuse:
            shower = np.where(self.first_event_in_shower <= event_num)[0][-1]
            reuse_num = event_num - self.first_event_in_shower[shower]
        else:
            shower = event_num

        objects = self._shower_objects[shower]

        array_offset = objects['array_offsets'].parse_data_field()[reuse_num]
        time_offset = objects['array_offsets'].time_offset

        photon_bunches = {}
        n_photons = []
        n_bunches = []
        for data in objects['telescope_data'][reuse_num]:
            if isinstance(data, IACTPhotons):
                photon_bunches[data.telescope] = data.parse_data_field()
                photon_bunches[data.telescope]['x']  # -= array_offset['x']
                photon_bunches[data.telescope]['y']  # -= array_offset['y']
                photon_bunches[data.telescope]['time']  # -= time_offset
                n_photons.append(data.n_photons)
                n_bunches.append(data.n_bunches)

        event = CorsikaEvent(
            header=objects['header'].parse_data_field(),
            end_block=objects['end_block'].parse_data_field(),
            photon_bunches=photon_bunches,
            time_offset=time_offset,
            x_offset=array_offset['x'],
            y_offset=array_offset['y'],
            weight=array_offset['weight'],
            event_number=event_num,
            shower=shower,
            reuse=reuse_num + 1,
            n_photons=np.array(n_photons),
            n_bunches=np.array(n_bunches),
        )

        return event


CorsikaEventTuple = namedtuple(
    'CorsikaEventTuple',
    [
        'header', 'end_block', 'photon_bunches',
        'time_offset', 'x_offset', 'y_offset', 'weight',
        'event_number', 'shower', 'reuse',
        'n_photons', 'n_bunches',
    ]
)


class CorsikaEvent(CorsikaEventTuple):
    '''
    A single event as simulated by corsika

    Members:
      event_number

      shower:
          the id of the simulated shower

      reuse:
          reuse index for this shower

      header:
        a dictionary containing the corsika event header

      end_block:
        numpy array of floats with the event end block data

      photon_bunches:
        a dictionary mapping telescope_ids to numpy
        arrays with the photon bunch data with the following colums:
          x:         x coordinate in cm
          y:         y coordinate in cm
          cx:        cosine of incident angle in x direction
          cy:        cosine of incident angle in y direction
          time:      time since first interaction in ns
          zem:       Emission height in cm above sea level
          lambda:    wavelength in nm
          scattered: indicates if the photon was scattered in the atmosphere

      time_offset:
        time from first interaction to ground in ns

      x_offset:
        array offset in x direction in cm

      y_offset:
        array offset in y direction in cm

      weight:
        weight for this offset position.
        Only different from 1 if importance sampling was used.
    '''
    def __repr__(self):
        return '{}(event_number={}, n_telescopes={}, n_photons={})'.format(
            self.__class__.__name__,
            self.event_number,
            len(self.n_bunches),
            self.n_photons,
        )
