import warnings
import logging

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

        if not isinstance(self._objects[0], CorsikaRunHeader):
            raise WrongTypeException('Object 0 is not a CORSIKA run header')
        self.header = self._objects[0].parse_data_field()

        if not isinstance(self._objects[1], CorsikaInputCard):
            raise WrongTypeException('Object 1 is not a CORSIKA input card')
        self.input_card = self._objects[1].parse_data_field()

        if not isinstance(self._objects[2], CorsikaTelescopeDefinition):
            raise WrongTypeException('Object 2 is not a CORSIKA telescope definition')
        self.num_telescopes = self._objects[2].num_telescopes
        self.telescope_positions = self._objects[2].parse_data_field()

        if not isinstance(self._objects[-1], CorsikaRunEndBlock):
            warnings.warn(
                'Last Object is not a CORSIKA Run End Block.'
                'The file seems to be truncated.'
            )
        else:
            self.end_block = self._objects[-1].parse_data_field()


class CorsikaEvent:
    pass
