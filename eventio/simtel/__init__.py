from ..base import KNOWN_OBJECTS, EventIOObject
from .objects import (
    TelescopeObject,
    RunHeader,
    MCRunHeader,
    CameraSettings,
    CameraOrganization,
    PixelSettings,
    DisabledPixels,
    CameraSoftwareSettings,
    PointingCorrection,
    DriveSettings,
    CentralEvent,
    TrackingPosition,
    TelescopeEvent,
    Event,
    TelescopeEventHeader,
    ADCSum,
    ADCSamples,
    ImageParameters,
    StereoReconstruction,
    PixelTiming,
    PixelCalibration,
    MCStereoReconstruction,
    MCEvent,
    CameraMonitoring,
    LaserCalibration,
    RunStatistics,
    MCRunStatistics,
    MCPhotoelectronSum,
    PixelList,
    CalibrationEvent,
)

__all__ = [
    'RunHeader',
    'MCRunHeader',
    'CameraSettings',
    'CameraOrganization',
    'PixelSettings',
    'DisabledPixels',
    'CameraSoftwareSettings',
    'PointingCorrection',
    'DriveSettings',
    'CentralEvent',
    'TrackingPosition',
    'TelescopeEvent',
    'Event',
    'TelescopeEventHeader',
    'ADCSum',
    'ADCSamples',
    'ImageParameters',
    'StereoReconstruction',
    'PixelTiming',
    'PixelCalibration',
    'MCStereoReconstruction',
    'MCEvent',
    'CameraMonitoring',
    'LaserCalibration',
    'RunStatistics',
    'MCRunStatistics',
    'MCPhotoelectronSum',
    'PixelList',
    'CalibrationEvent',
]

for cls in EventIOObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for cls in TelescopeObject.__subclasses__():
    KNOWN_OBJECTS[cls.eventio_type] = cls

for tel_id in range(1000):
    KNOWN_OBJECTS[TelescopeEvent.telid_to_type(tel_id)] = TelescopeEvent

for tel_id in range(1000):
    KNOWN_OBJECTS[TrackingPosition.telid_to_type(tel_id)] = TrackingPosition
