from ..base import KNOWN_OBJECTS, EventIOObject
from .objects import (
    TelescopeObject,
    SimTelRunHeader,
    SimTelMCRunHeader,
    SimTelCamSettings,
    SimTelCamOrgan,
    SimTelPixelset,
    SimTelPixelDisable,
    SimTelCamsoftset,
    SimTelPointingCor,
    SimTelTrackSet,
    SimTelCentEvent,
    SimTelTrackEvent,
    SimTelTelEvent,
    SimTelEvent,
    SimTelTelEvtHead,
    SimTelTelADCSum,
    SimTelTelADCSamp,
    SimTelTelImage,
    SimTelShower,
    SimTelPixelTiming,
    SimTelPixelCalib,
    SimTelMCShower,
    SimTelMCEvent,
    SimTelTelMoni,
    SimTelLasCal,
    SimTelRunStat,
    SimTelMCRunStat,
    SimTelMCPeSum,
    SimTelPixelList,
    SimTelCalibEvent,
)

__all__ = [
    'SimTelRunHeader',
    'SimTelMCRunHeader',
    'SimTelCamSettings',
    'SimTelCamOrgan',
    'SimTelPixelset',
    'SimTelPixelDisable',
    'SimTelCamsoftset',
    'SimTelPointingCor',
    'SimTelTrackSet',
    'SimTelCentEvent',
    'SimTelTrackEvent',
    'SimTelTelEvent',
    'SimTelEvent',
    'SimTelTelEvtHead',
    'SimTelTelADCSum',
    'SimTelTelADCSamp',
    'SimTelTelImage',
    'SimTelShower',
    'SimTelPixelTiming',
    'SimTelPixelCalib',
    'SimTelMCShower',
    'SimTelMCEvent',
    'SimTelTelMoni',
    'SimTelLasCal',
    'SimTelRunStat',
    'SimTelMCRunStat',
    'SimTelMCPeSum',
    'SimTelPixelList',
    'SimTelCalibEvent',
]

for cls in EventIOObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for cls in TelescopeObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for tel_id in range(1000):
    KNOWN_OBJECTS[SimTelTelEvent.telid_to_type(tel_id)] = SimTelTelEvent

for tel_id in range(1000):
    KNOWN_OBJECTS[SimTelTrackEvent.telid_to_type(tel_id)] = SimTelTrackEvent
