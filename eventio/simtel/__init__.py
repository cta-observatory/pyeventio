from ..base import KNOWN_OBJECTS, EventIOObject
from .simtelfile import SimTelFile
from .objects import (
    ADCSamples,
    ADCSums,
    ArrayEvent,
    AuxiliaryAnalogTraces,
    AuxiliaryDigitalTraces,
    CalibrationEvent,
    CameraMonitoring,
    CameraOrganization,
    CameraSettings,
    CameraSoftwareSettings,
    DisabledPixels,
    DriveSettings,
    FSPhot,
    History,
    HistoryCommandLine,
    HistoryConfig,
    ImageParameters,
    LaserCalibration,
    MCEvent,
    MCPhotoelectronSum,
    MCRunHeader,
    MCRunStatistics,
    MCShower,
    PixelCalibration,
    PixelList,
    PixelSettings,
    PixelTiming,
    PixelTriggerTimes,
    PointingCorrection,
    RunHeader,
    RunStatistics,
    StereoReconstruction,
    TelescopeEvent,
    TelescopeEventHeader,
    TelescopeObject,
    TrackingPosition,
    TriggerInformation,
)

__all__ = [
    'ADCSamples',
    'ADCSums',
    'ArrayEvent',
    'AuxiliaryAnalogTraces',
    'AuxiliaryDigitalTraces',
    'CalibrationEvent',
    'CameraMonitoring',
    'CameraOrganization',
    'CameraSettings',
    'CameraSoftwareSettings',
    'DisabledPixels',
    'DriveSettings',
    'FSPhot',
    'History',
    'HistoryCommandLine',
    'HistoryConfig',
    'ImageParameters',
    'LaserCalibration',
    'MCEvent',
    'MCPhotoelectronSum',
    'MCRunHeader',
    'MCRunStatistics',
    'MCShower',
    'PixelCalibration',
    'PixelList',
    'PixelSettings',
    'PixelTiming',
    'PixelTriggerTimes',
    'PointingCorrection',
    'RunHeader',
    'RunStatistics',
    'SimTelFile',
    'StereoReconstruction',
    'TelescopeEvent',
    'TelescopeEventHeader',
    'TrackingPosition',
    'TriggerInformation',
]

for cls in EventIOObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for cls in TelescopeObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for tel_id in range(1000):
    KNOWN_OBJECTS[TelescopeEvent.telid_to_type(tel_id)] = TelescopeEvent

for tel_id in range(1000):
    KNOWN_OBJECTS[TrackingPosition.telid_to_type(tel_id)] = TrackingPosition
