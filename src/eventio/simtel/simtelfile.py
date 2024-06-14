'''
Implementation of an EventIOFile that
loops through SimTel Array events.
'''
from functools import lru_cache
import re
from copy import copy
from collections import defaultdict
import warnings
import logging
from typing import Dict, Any

from ..base import EventIOFile
from ..exceptions import check_type
from .. import iact
from ..histograms import Histograms
from .objects import (
    ADCSamples,
    ADCSums,
    ArrayEvent,
    CalibrationEvent,
    CameraMonitoring,
    CameraOrganization,
    CameraSettings,
    CameraSoftwareSettings,
    DisabledPixels,
    DriveSettings,
    History,
    HistoryMeta,
    ImageParameters,
    LaserCalibration,
    MCEvent,
    MCPhotoelectronSum,
    MCRunHeader,
    MCShower,
    PixelList,
    PixelSettings,
    PixelTiming,
    PixelTriggerTimes,
    PixelMonitoring,
    PointingCorrection,
    RunHeader,
    TelescopeEvent,
    TelescopeEventHeader,
    TrackingPosition,
    TriggerInformation,
    CalibrationPhotoelectrons,
)


telescope_descriptions_types = (
    CameraSettings,
    CameraOrganization,
    PixelSettings,
    DisabledPixels,
    CameraSoftwareSettings,
    DriveSettings,
    PointingCorrection,
)


class UnknownObjectWarning(UserWarning):
    pass


log = logging.getLogger(__name__)


camel_re1 = re.compile('(.)([A-Z][a-z]+)')
camel_re2 = re.compile('([a-z0-9])([A-Z])')


# these objects mark the end of the current event
NEXT_EVENT_MARKERS = (
    MCEvent, MCShower, CalibrationEvent, CalibrationPhotoelectrons, type(None)
)


@lru_cache()
def camel_to_snake(name):
    s1 = camel_re1.sub(r'\1_\2', name)
    return camel_re2.sub(r'\1_\2', s1).lower()


class NoTrackingPositions(Exception):
    pass


class SimTelFile:
    '''
    This assumes the following top-level structure once events are seen:

    Either:
    MCShower[2020]
    MCEvent[2021]
      # stuff belonging to this MCEvent
      optional TelescopeData[1204]
      optional PixelMonitoring[2033] for each telescope
      optional (CameraMonitoring[2022], LaserCalibration[2023]) for each telescope
      optional MCPhotoelectronSum[2026]
      optional ArrayEvent[2010]

    optional MCEvent for same shower (reuse)

    Or:
    CalibrationEvent[2028]

    with possibly more CameraMonitoring / LaserCalibration in between
    calibration events
    '''
    def __init__(
        self,
        path,
        skip_non_triggered=True,
        skip_calibration=False,
        allowed_telescopes=None,
        zcat=True,
    ):
        self._file = EventIOFile(path, zcat=zcat)
        self.path = path

        self.skip_calibration = skip_calibration
        self.skip_non_triggered = skip_non_triggered

        self.allowed_telescopes = None
        if allowed_telescopes:
            self.allowed_telescopes = set(allowed_telescopes)

        # object storage
        self.histograms = None
        self.history = []
        self.mc_run_headers = []
        self.corsika_inputcards = []
        self.atmospheric_profiles = []
        self.header = None
        self.n_telescopes = None
        self.telescope_meta = {}
        self.global_meta = {}
        self.telescope_descriptions = defaultdict(dict)
        self.pixel_monitorings = defaultdict(dict)
        self.camera_monitorings = defaultdict(dict)
        self.laser_calibrations = defaultdict(dict)

        # wee need to keep the mc_shower separate from the event,
        # as it is valid for more than one (CORSIKA re-use)
        self.current_mc_shower = None
        self.current_mc_shower_id = None
        self.current_event_id = None
        self.current_event = {"type": "data"}

        # read the header:
        # assumption: the header is done when
        # any of the objects in check is not None anymore
        # and we found the telescope_descriptions of all telescopes
        check = []
        found_all_telescopes = False
        while not (any(o is not None for o in check) and found_all_telescopes):
            self._parse_next_object()

            check = [
                self.current_mc_shower,
                self.current_event_id,
                self.laser_calibrations,
                self.camera_monitorings,
            ]

            # check if we found all the descriptions of all telescopes
            if self.n_telescopes is not None:
                found = sum(
                    len(t) == len(telescope_descriptions_types)
                    for t in self.telescope_descriptions.values()
                )
                found_all_telescopes = found == self.n_telescopes

    def __iter__(self):
        '''
        Iterate over all events in the file.
        '''
        return self

    def __next__(self):
        event = self._read_next_event()

        while self._check_skip(event):
            event = self._read_next_event()

        return event

    def _read_next_event(self):
        if self._file.peek() is None:
            raise StopIteration()

        while isinstance(self._file.peek(), (PixelMonitoring, CameraMonitoring, LaserCalibration)):
            self._parse_next_object()

        if isinstance(self._file.peek(), CalibrationPhotoelectrons):
            self._parse_next_object()

        if isinstance(self._file.peek(), MCShower):
            self._parse_next_object()

        if isinstance(self._file.peek(), (MCEvent, CalibrationEvent)):
            self._parse_next_object()
            self._read_until_next_event()
            return self._build_event()

        # extracted calibration events have "naked" ArrayEvents without
        # a preceding MCEvent or CalibrationEvent wrapper
        if isinstance(self._file.peek(), ArrayEvent):
            self._parse_next_object()
            return self._build_event()

        raise ValueError(f"Unexpected obj type: {self._file.peek()}")

    def _check_skip(self, event):
        if event['type'] == 'data':
            return self.skip_non_triggered and not event.get('telescope_events')

        if event['type'] == 'calibration':
            return self.skip_calibration

        raise ValueError(f'Unexpected event type {event["type"]}')

    def _read_until_next_event(self):
        while not isinstance(self._file.peek(), NEXT_EVENT_MARKERS):
            self._parse_next_object()

    def _parse_next_object(self):
        o = next(self._file)

        # order of if statements is roughly sorted
        # by the number of occurences in a simtel file
        # this should minimize the number of if statements evaluated

        if isinstance(o, MCEvent):
            self.current_event["event_id"] = o.header.id
            self.current_event["mc_event"] = o.parse()

        elif isinstance(o, MCShower):
            self.current_mc_shower = o.parse()
            self.current_mc_shower_id = o.header.id

        elif isinstance(o, ArrayEvent):
            self.current_event_id = o.header.id
            self.current_event["event_id"] = o.header.id
            self.current_event.update(
                parse_array_event(o, self.allowed_telescopes)
            )

        elif isinstance(o, iact.TelescopeData):
            self.current_event.update(parse_telescope_data(o))

        elif isinstance(o, MCPhotoelectronSum):
            self.current_event["photoelectron_sums"] = o.parse()

        elif isinstance(o, CameraMonitoring):
            self.camera_monitorings[o.telescope_id].update(o.parse())

        elif isinstance(o, LaserCalibration):
            self.laser_calibrations[o.telescope_id].update(o.parse())

        elif isinstance(o, PixelMonitoring):
            self.pixel_monitorings[o.telescope_id].update(o.parse())

        elif isinstance(o, telescope_descriptions_types):
            key = camel_to_snake(o.__class__.__name__)
            self.telescope_descriptions[o.telescope_id][key] = o.parse()

        elif isinstance(o, RunHeader):
            self.header = o.parse()
            self.n_telescopes = self.header['n_telescopes']

        elif isinstance(o, MCRunHeader):
            self.mc_run_headers.append(o.parse())

        elif isinstance(o, iact.InputCard):
            self.corsika_inputcards.append(o.parse())

        elif isinstance(o, CalibrationEvent):
            array_event = next(o)
            # make event_id negative for calibration events to not overlap with
            # later air shower events
            self.current_event["event_id"] = -array_event.header.id
            self.current_event_id = self.current_event["event_id"]
            self.current_event.update(
                parse_array_event(array_event, self.allowed_telescopes)
            )
            self.current_event['type'] = 'calibration'
            self.current_event['calibration_type'] = o.type

        elif isinstance(o, CalibrationPhotoelectrons):
            telescope_data = next(o)
            if not isinstance(telescope_data, iact.TelescopeData):
                warnings.warn(
                    f"Unexpected sub-object: {telescope_data} in {o}, ignoring",
                    UnknownObjectWarning
                )
                return

            self.current_event["photoelectrons"] = {}
            for photoelectrons in telescope_data:
                if not isinstance(photoelectrons, iact.PhotoElectrons):
                    warnings.warn(
                        f"Unexpected sub-object: {photoelectrons} in {telescope_data}, ignoring",
                        UnknownObjectWarning
                    )

                tel_id = photoelectrons.telescope_id
                self.current_event["photoelectrons"][tel_id] = photoelectrons.parse()

        elif isinstance(o, History):
            for sub in o:
                self.history.append(sub.parse())

        elif isinstance(o, HistoryMeta):
            if o.header.id == -1:
                self.global_meta = o.parse()
            else:
                self.telescope_meta[o.header.id] = o.parse()

        elif isinstance(o, Histograms):
            self.histograms = o.parse()
        elif isinstance(o, iact.AtmosphericProfile):
            self.atmospheric_profiles.append(o.parse())
        else:
            warnings.warn(
                'object type encountered, which is no handled'
                ' at the moment: {}'.format(o),
                UnknownObjectWarning,
            )

    def _build_event(self):
        '''check if all necessary info for an event was found,
        then make an event and invalidate old data
        '''
        event = self.current_event
        self.current_event: Dict[str, Any] = {"type": "data"}

        if self.current_mc_shower is not None and event["type"] == "data":
            event["mc_shower"] = self.current_mc_shower

        # fill monitoring info if we have telescope events
        if 'telescope_events' in event:
            tel_ids = event["telescope_events"].keys()
            event['camera_monitorings'] = {
                telescope_id: copy(self.camera_monitorings[telescope_id])
                for telescope_id in tel_ids
            }
            event['laser_calibrations'] = {
                telescope_id: copy(self.laser_calibrations[telescope_id])
                for telescope_id in tel_ids
            }

            event['pixel_monitorings'] = {
                telescope_id: copy(self.pixel_monitorings[telescope_id])
                for telescope_id in tel_ids
            }

        return event

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._file.close()

    def tell(self):
        return self._file.tell()

    def seek(self, *args, **kwargs):
        return self._file.seek(*args, **kwargs)


def parse_array_event(array_event, allowed_telescopes=None):
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
    # for older files, the array_event.header.id does not match the mc event id
    # so we overwrite it later with the event id in the trigger information
    event_id = array_event.header.id

    for i, o in enumerate(array_event):
        # require first element to be a TriggerInformation
        if i == 0:
            check_type(o, TriggerInformation)
            # extracted calibration events seem to have a valid event id in the array event
            # but not in the trigger
            if o.header.id != 0:
                event_id = o.header.id
            trigger_information = o.parse()
            telescopes = set(trigger_information['telescopes_with_data'])

            if allowed_telescopes and len(telescopes & allowed_telescopes) == 0:
                break

        elif isinstance(o, TelescopeEvent):
            if allowed_telescopes is None or o.telescope_id in allowed_telescopes:
                telescope_events[o.telescope_id] = parse_telescope_event(o)

        elif isinstance(o, TrackingPosition):
            if allowed_telescopes is None or o.telescope_id in allowed_telescopes:
                tracking_positions[o.telescope_id] = o.parse()

    missing_tracking = set(telescope_events.keys()) - set(tracking_positions.keys())
    if missing_tracking:
        raise NoTrackingPositions(
            'Missing tracking positions for telescopes {}'.format(
                missing_tracking
            )
        )

    return {
        'event_id': event_id,
        'trigger_information': trigger_information,
        'telescope_events': telescope_events,
        'tracking_positions': tracking_positions,
    }


def parse_telescope_data(telescope_data):
    ''' Parse the TelescopeData block with Cherenkov Photon information'''
    check_type(telescope_data, iact.TelescopeData)

    data = defaultdict(dict)
    for o in telescope_data:
        if isinstance(o, iact.PhotoElectrons):
            data["photoelectrons"][o.telescope_id] = o.parse()
        elif isinstance(o, iact.Photons):
            p, e = o.parse()
            data["photons"][o.telescope_id] = p
            if e is not None:
                data["emitter"][o.telescope_id] = e
    return data


def parse_telescope_event(telescope_event):
    '''Parse a telescope event'''
    check_type(telescope_event, TelescopeEvent)

    event = {'pixel_lists': {}}
    for i, o in enumerate(telescope_event):

        if i == 0:
            check_type(o, TelescopeEventHeader)
            event['header'] = o.parse()

        elif isinstance(o, ADCSamples):
            event['adc_samples'] = o.parse()

        elif isinstance(o, ADCSums):
            event['adc_sums'] = o.parse()

        elif isinstance(o, PixelTiming):
            event['pixel_timing'] = o.parse()

        elif isinstance(o, ImageParameters):
            event['image_parameters'] = o.parse()

        elif isinstance(o, PixelList):
            event['pixel_lists'][o.code] = o.parse()

        elif isinstance(o, PixelTriggerTimes):
            event['pixel_trigger_times'] = o.parse()

    return event
