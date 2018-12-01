import logging
from collections import namedtuple

from ..base import KNOWN_OBJECTS, EventIOFile, EventIOObject
from ..exceptions import check_type

from .objects import (
    CORSIKARunHeader,
    CORSIKATelescopeDefinition,
    CORSIKAEventHeader,
    CORSIKAArrayOffsets,
    CORSIKATelescopeData,
    IACTPhotons,
    IACTLayout,
    IACTTriggerTime,
    IACTPhotoElectrons,
    CORSIKAEventEndBlock,
    CORSIKARunEndBlock,
    CORSIKALongitudinal,
    CORSIKAInputCard,
)


for o in EventIOObject.__subclasses__():
    KNOWN_OBJECTS[o.eventio_type] = o

log = logging.getLogger(__name__)


class IACTFile(EventIOFile):
    '''
    An Interface to access the data of a EventIO file
    as produced by the CORSIKA IACT (a.k.a. bernlohr) extension
    more easily.

    Instead of low-level access to eventio items, it provides
    direct access to telescope events and simulation settings.

    It is an Iterable of `CORSIKAEvent`s.

    Notes
    -----
    Calling `next` on this file will give you the next low-level EventIOObject.
    Calling `next(iter(IACTFile))` will give you the next event.

    The structure of an IACT EventIO file is assumed to be like this:

    CORSIKARunHeader
    CORSIKAInputCard
    CORSIKATelescopeDefinition

    For each Event:
      CORSIKAEventHeader
      CORSIKAArrayOffsets
      CORSIKALongitudinal (optional)
      For each reuse:
        CORSIKATelescopeData
        For each Telescope:
          IACTPhotons
      CORSIKAEventEndBlock

    CORSIKARunEndBlock
    '''

    def __init__(self, path):
        super().__init__(path)

        header_object = next(self)
        check_type(header_object, CORSIKARunHeader)
        self.header = header_object.parse_data_field()

        input_card_object = next(self)
        check_type(input_card_object, CORSIKAInputCard)
        self.input_card = input_card_object.parse_data_field()

        telescope_object = next(self)
        check_type(telescope_object, CORSIKATelescopeDefinition)

        self.n_telescopes = telescope_object.n_telescopes
        self.telescope_positions = telescope_object.parse_data_field()
        self._first_event_byte = self.tell()

    def __repr__(self):
        return (
            '{}(\n'
            '  path={}\n'
            '  n_telescopes={}\n'
            ')'
        ).format(
            self.__class__.__name__,
            self.path,
            self.n_telescopes,
        )

    def __iter__(self):
        '''
        Generator over the single array events
        '''
        self._next_header_pos = self._first_event_byte
        obj = next(self)

        while not isinstance(obj, CORSIKARunEndBlock):
            check_type(obj, CORSIKAEventHeader)
            header = obj.parse_data_field()

            reuse_object = next(self)
            check_type(reuse_object, CORSIKAArrayOffsets)

            n_reuses = reuse_object.n_reuses
            array_offsets = reuse_object.parse_data_field()
            time_offset = reuse_object.time_offset

            obj = next(self)
            if isinstance(obj, CORSIKALongitudinal):
                longitudinal = obj.parse_data_field()
                obj = next(self)
            else:
                longitudinal = None

            for reuse in range(n_reuses):

                check_type(obj, CORSIKATelescopeData)
                telescope_data_obj = obj

                photon_bunches = {}
                n_photons = {}
                n_bunches = {}
                for data in telescope_data_obj:
                    if isinstance(data, IACTPhotons):
                        photon_bunches[data.telescope] = data.parse_data_field()
                        n_photons[data.telescope] = data.n_photons
                        n_bunches[data.telescope] = data.n_bunches

                yield CORSIKAEvent(
                    header=header,
                    photon_bunches=photon_bunches,
                    time_offset=time_offset,
                    x_offset=array_offsets[reuse]['x'],
                    y_offset=array_offsets[reuse]['y'],
                    weight=array_offsets[reuse]['weight'],
                    event_id=header.event_id,
                    reuse=reuse + 1,
                    n_photons=n_photons,
                    n_bunches=n_bunches,
                    longitudinal=longitudinal,
                )
                obj = next(self)

            check_type(obj, CORSIKAEventEndBlock)

            obj = next(self)

        self.run_end = obj.parse_data_field()


CORSIKAEventTuple = namedtuple(
    'CORSIKAEventTuple',
    [
        'header', 'photon_bunches',
        'time_offset', 'x_offset', 'y_offset', 'weight',
        'event_id', 'reuse',
        'n_photons', 'n_bunches',
        'longitudinal',
    ]
)


class CORSIKAEvent(CORSIKAEventTuple):
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
        return '{}(event_id={}, reuse={}, n_telescopes={}, n_photons={})'.format(
            self.__class__.__name__,
            self.event_id,
            self.reuse,
            len(self.n_bunches),
            self.n_photons,
        )
