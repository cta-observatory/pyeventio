'''
Implementation of an EventIOFile that
loops through SimTel Array events.
'''
import re
from copy import copy
from collections import defaultdict
import logging
import warnings
from ..base import EventIOFile
from ..exceptions import check_type
from .. import iact
from ..histograms import Histograms
from .objects import (
    ADCSamples,
    ADCSums,
    ArrayEvent,
    CameraMonitoring,
    CameraOrganization,
    CameraSettings,
    CameraSoftwareSettings,
    TriggerInformation,
    DisabledPixels,
    DriveSettings,
    History,
    ImageParameters,
    LaserCalibration,
    MCEvent,
    MCPhotoelectronSum,
    MCRunHeader,
    MCShower,
    PixelList,
    PixelSettings,
    PixelTiming,
    PointingCorrection,
    RunHeader,
    TelescopeEvent,
    TelescopeEventHeader,
    TrackingPosition,
)


log = logging.getLogger(__name__)


camel_re1 = re.compile('(.)([A-Z][a-z]+)')
camel_re2 = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(name):
    s1 = camel_re1.sub(r'\1_\2', name)
    return camel_re2.sub(r'\1_\2', s1).lower()


class NoTrackingPositions(Exception):
    pass


class SimTelFile(EventIOFile):
    def __init__(self, path):
        super().__init__(path)

        self.path = path

        self.history = []
        o = next(self)
        while isinstance(o, History):
            self.history.append(o)
            o = next(self)

        check_type(o, RunHeader)
        self.header = o.parse_data_field()
        self.n_telescopes = self.header['n_telescopes']

        o = next(self)
        self.mc_header = []
        while isinstance(o, MCRunHeader):
            self.mc_header.append(o.parse_data_field())
            o = next(self)

        self.corsika_inputcards = []
        while isinstance(o, iact.InputCard):
            self.corsika_inputcards.append(o.parse_data_field())
            o = next(self)

        expected_structure = [
            CameraSettings,
            CameraOrganization,
            PixelSettings,
            DisabledPixels,
            CameraSoftwareSettings,
            DriveSettings,
            PointingCorrection,
        ]

        self.telescope_descriptions = defaultdict(dict)
        first = True
        for i in range(self.n_telescopes):
            for eventio_type in expected_structure:
                if not first:
                    o = next(self)
                first = False

                while not isinstance(o, eventio_type):
                    msg = 'Skipping unexpected object of type {}'.format(
                        o.__class__.__name__
                    )
                    warnings.warn(msg)
                    log.warn(msg)
                    o = next(self)

                key = camel_to_snake(o.__class__.__name__)
                self.telescope_descriptions[o.telescope_id][key] = o.parse_data_field()

        self.shower = None
        self.camera_monitoring = {}  # tel_id: CameraMonitoring
        self.laser_calibration = {}  # tel_id: LaserCalibration
        self._first_event_byte = self.tell()

    def __iter__(self):
        self._next_header_pos = self._first_event_byte

        current_mc_shower = None
        current_mc_event = None
        current_photoelectron_sum = None
        current_photoelectrons = None
        camera_monitorings = defaultdict(dict)
        laser_calibrations = defaultdict(dict)

        o = next(self)

        while True:
            if isinstance(o, MCShower):
                current_mc_shower = o.parse_data_field()

            elif isinstance(o, MCEvent):
                current_mc_event = o.parse_data_field()

            elif isinstance(o, iact.TelescopeData):
                current_photoelectrons = parse_photoelectrons(o)

            elif isinstance(o, MCPhotoelectronSum):
                current_photoelectron_sum = o.parse_data_field()

            elif isinstance(o, ArrayEvent):
                array_event = parse_array_event(o)
                event_data = {
                    'mc_shower': current_mc_shower,
                    'mc_event': current_mc_event,
                    'array_event': array_event,
                    'photoelectron_sums': current_photoelectron_sum,
                    'photoelectrons': current_photoelectrons,
                }
                event_data['camera_monitorings'] = {
                    telescope_id: copy(camera_monitorings[telescope_id])
                    for telescope_id in array_event['telescope_events'].keys()
                }
                event_data['laser_calibrations'] = {
                    telescope_id: copy(laser_calibrations[telescope_id])
                    for telescope_id in array_event['telescope_events'].keys()
                }
                yield event_data

            elif isinstance(o, CameraMonitoring):
                camera_monitorings[o.telescope_id].update(o.parse_data_field())

            elif isinstance(o, LaserCalibration):
                laser_calibrations[o.telescope_id].update(o.parse_data_field())

            elif isinstance(o, Histograms):
                self.histograms = o.parse_data_field()
                break

            o = next(self)


def parse_array_event(array_event):
    '''structure of event:
        TriggerInformation[2009]  <-- this knows how many TelescopeEvents

        TelescopeEvent[2202]
        ...
        TelescopeEvent[2208]

        TrackingPosition[2101]
        ...
        TrackingPosition[2164]

        StereoReconstruction[2015]


        In words:
            1 cent event
            n tel events
            m track events (n does not need to be == m)
            1 shower
    '''
    check_type(array_event, ArrayEvent)

    telescope_events = {}
    tracking_positions = {}

    for i, o in enumerate(array_event):
        # require first element to be a TriggerInformation
        if i == 0:
            check_type(o, TriggerInformation)
            trigger_information = o.parse_data_field()

        elif isinstance(o, TelescopeEvent):
            telescope_events[o.telescope_id] = parse_telescope_event(o)

        elif isinstance(o, TrackingPosition):
            tracking_positions[o.telescope_id] = o.parse_data_field()

    missing_tracking = set(telescope_events.keys()) - set(tracking_positions.keys())
    if missing_tracking:
        raise NoTrackingPositions(
            'Missing tracking positions for telescopes {}'.format(
                missing_tracking
            )
        )

    return {
        'trigger_information': trigger_information,
        'telescope_events': telescope_events,
        'tracking_positions': tracking_positions,
    }


def parse_photoelectrons(telescope_data):
    check_type(telescope_data, iact.TelescopeData)

    photo_electrons = {}
    for o in telescope_data:
        check_type(o, iact.PhotoElectrons)
        photo_electrons[o.telescope_id] = o.parse_data_field()

    return photo_electrons


def parse_telescope_event(telescope_event):
    '''Parse a telescope event'''
    check_type(telescope_event, TelescopeEvent)

    event = {}
    for i, o in enumerate(telescope_event):

        if i == 0:
            check_type(o, TelescopeEventHeader)
            event['header'] = o.parse_data_field()

        elif isinstance(o, ADCSamples):
            event['adc_samples'] = o.parse_data_field()

        elif isinstance(o, ADCSums):
            event['adc_sums'] = o.parse_data_field()

        elif isinstance(o, PixelTiming):
            event['pixel_timing'] = o.parse_data_field()

        elif isinstance(o, ImageParameters):
            event['image_parameters'] = o.parse_data_field()

        elif isinstance(o, PixelList):
            event['pixel_list'] = o.parse_data_field()

    return event
