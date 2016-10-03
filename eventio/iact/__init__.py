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


class IACTFile(EventIOFile):
    '''
    An Interface to access the data of a EventIO file
    as produced by the CORSIKA IACT (a.k.a. bernlohr) extension
    more easily.

    Instead of low-level access to eventio items, it provides
    direct access to telescope events and simulation settings.

    For example, it iterates over CorsikaEvent instances and
    IACTFile[n] will return the nth event in the file.
    '''

    def __init__(self, path):
        super().__init__(path)

        if not isinstance(self._objects[0], CorsikaRunHeader):
            raise WrongTypeException('Object 0 is not a CORSIKA Run Header')

        if not isinstance(self._objects[1], CorsikaInputCard):
            raise WrongTypeException('Object 1 is not a CORSIKA Input Card')

        self.run_header = self._objects[0].parse_data_field()
        self.input_card = self._objects[1].parse_data_field()


class CorsikaEvent:
    pass
