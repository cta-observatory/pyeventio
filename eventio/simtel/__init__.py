from ..base import KNOWN_OBJECTS, EventIOObject
from .simtelfile import SimTelFile
from .objects import (
    History,
    HistoryConfig,
    HistoryCommandLine,
    ADCSamples,
    ADCSums,
    ArrayEvent,
    CalibrationEvent,
    CameraMonitoring,
    CameraOrganization,
    CameraSettings,
    CameraSoftwareSettings,
    TriggerInformation,
    DisabledPixels,
    DriveSettings,
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
    PointingCorrection,
    RunHeader,
    RunStatistics,
    StereoReconstruction,
    TelescopeEvent,
    TelescopeEventHeader,
    TelescopeObject,
    TrackingPosition,
)

__all__ = [
    'History',
    'HistoryCommandLine',
    'HistoryConfig',
    'SimTelFile',
    'ADCSamples',
    'ADCSums',
    'ArrayEvent',
    'CalibrationEvent',
    'CameraMonitoring',
    'CameraOrganization',
    'CameraSettings',
    'CameraSoftwareSettings',
    'TriggerInformation',
    'DisabledPixels',
    'DriveSettings',
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
    'PointingCorrection',
    'RunHeader',
    'RunStatistics',
    'StereoReconstruction',
    'TelescopeEvent',
    'TelescopeEventHeader',
    'TrackingPosition',
]

for cls in EventIOObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for cls in TelescopeObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for tel_id in range(1000):
    KNOWN_OBJECTS[TelescopeEvent.telid_to_type(tel_id)] = TelescopeEvent

for tel_id in range(1000):
    KNOWN_OBJECTS[TrackingPosition.telid_to_type(tel_id)] = TrackingPosition
