'''
File for reading the event output of sim_telarray.
'''
from functools import cache
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
    AuxiliaryAnalogTraces,
    AuxiliaryDigitalTraces,
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
    StereoReconstruction,
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


@cache
def camel_to_snake(name):
    s1 = camel_re1.sub(r'\1_\2', name)
    return camel_re2.sub(r'\1_\2', s1).lower()


class NoTrackingPositions(Exception):
    pass


class SimTelFile:
    '''
    A class to read files produced by sim_telarray.

    This class is an iterator over simulated air shower events.

    It assumes the following top-level structure, elements with ? are optional.

    First, a header that appears once in the beginning of the file:
    - History[70]
    - HistoryMeta[75]?
    - one for each telescope:
        - HistoryMeta[75]?
    - RunHeader[2000]
    - MCRunHeader[2001]?
    - InputCard[1212]?
    - AtmosphericProfile[1216]?
    - one block of these types for each telescope:
        - CameraSettings[2002]
        - CameraOrganization[2003]
        - PixelSettings[2004]
        - DisabledPixels[2005]
        - CameraSoftwareSettings[2006]
        - DriveSettings[2008]
        - PointingCorrection[2007]

    This concludes the "header" information, what follows are events.

    - Optionally, a number of calibration events, in that case,
      also the calibration info comes now:
        - once, one block of these types for each telescope:
            - CameraMonitoring[2022]
            - LaserCalibration[2023]
        - then the number of simulated calibration events:
            - CalibrationPhotoelectrons[2034]?
            - CalibrationEvent[2028]
              - ArrayEvent[2010] # see below for content of array event

    Now follows the main payload of simulated events, for each simulated air shower:

    - MCShower[2020]
    - Photons[1205]?, particles at observation level
    - for each re-use of this shower:
      - MCEvent[2021]
      - TelescopeData[1204]?
      - before the first actually triggered event,
        only in case no calibration events were simulated,
        once, one block of these types for each telescope:
            - CameraMonitoring[2022]
            - LaserCalibration[2023]
      - MCPhotoelectronSum[2026]?
      - ArrayEvent[2010]?

    At the end of the file comes the Histograms object
    with summary statistics about the simulated events:
    - Histograms[100]

    Each ArrayEvent[2010] is assumed to have the following structure:
    - ArrayEvent[2010]
      - TriggerInformation[2009]
      - for each triggered telescope:
        - TelescopeEvent[type], the type encodes the telescope id
          - TelescopeEventHeader[2201]
          - ADCSamples[2013]?
          - ADCSums[2012]?
          - ImageParameters[2014]?
          - PixelTiming[2016]?
          - multiple possible:
            - PixelList[2027]?
          - PixelTriggerTimes[2032]?
          - multiple possible:
            - AuxiliaryDigitalTraces[2029]?
            - AuxiliaryAnalogTraces[2030]?
      - for each telescope:
        - TrackingPosition[type], the type encodes the telescope id
      - StereoReconstruction[2015]?
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

        # we need to keep the mc_shower separate from the event,
        # as it is valid for more than one (CORSIKA re-use)
        self.current_mc_shower = None
        self.current_obslev_particles = None
        self.current_event = None
        self._current_calib_pe = None
        self._finished = False

        # read the header:
        # assumption: the header is done when
        # any of the objects in check is not None anymore
        # and we found the telescope_descriptions of all telescopes
        found_all_telescopes = False
        while not found_all_telescopes:
            self._parse_next_object()

            # check if we found all the descriptions of all telescopes
            if self.n_telescopes is not None:
                found = sum(
                    len(t) == len(telescope_descriptions_types)
                    for t in self.telescope_descriptions.values()
                )
                found_all_telescopes = found == self.n_telescopes

    def __iter__(self):
        '''Iterate over all events in the file.'''
        return self

    def __next__(self):
        '''Get next event in the file.'''
        event = self._read_next_event()

        while self._check_skip(event):
            event = self._read_next_event()

        return event

    def _read_next_event(self):
        if self._finished:
            raise StopIteration

        try:
            event = None
            while event is None:
                event = self._parse_next_object()
            return event
        except (EOFError, StopIteration) as e:
            if isinstance(e, EOFError):
                warnings.warn(str(e))

            self._finished = True

            # in case we have event data in a truncated file, try returning what is there
            if self.current_event is not None:
                event = self.current_event
                self.current_event = None
                return event
            else:
                raise StopIteration

    def _check_skip(self, event):
        if event['type'] == 'data':
            return self.skip_non_triggered and not event.get('telescope_events')

        if event['type'] == 'calibration':
            return self.skip_calibration

        raise ValueError(f'Unexpected event type {event["type"]}')

    def _parse_next_object(self):
        o = next(self._file)
        event = None

        # order of if statements is roughly sorted
        # by the number of occurences in a simtel file
        # this should minimize the number of if statements evaluated
        if isinstance(o, MCEvent):
            # a new event started, return previous
            event = self.current_event
            # setup new event
            self.current_event = {
                "type": "data",
                "event_id": o.header.id,
                "mc_shower": self.current_mc_shower,
                "mc_event": o.parse(),
            }
            if self.current_obslev_particles is not None:
                self.current_event["observation_level_particles"] = self.current_obslev_particles

        elif isinstance(o, MCShower):
            self.current_mc_shower = o.parse()

        elif isinstance(o, ArrayEvent):
            # assume that array event without shower available are unpacked calibration events
            if self.current_mc_shower is None:
                event = self.current_event
                self.current_event = {"type": "calibration"}

            self.current_event["event_id"] = o.header.id
            self.current_event.update(
                parse_array_event(o, self.allowed_telescopes)
            )
            self._add_monitoring(self.current_event)

        elif isinstance(o, iact.TelescopeData):
            self.current_event.update(parse_telescope_data(o))

        elif isinstance(o, MCPhotoelectronSum):
            self.current_event["photoelectron_sums"] = o.parse()

        elif isinstance(o, iact.Photons):
            self.current_obslev_particles = o.parse()

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
            event = self.current_event
            self.current_event = {
                "type": "calibration",
                "event_id": -array_event.header.id,
                "calibration_type": o.type,
            }
            self.current_event.update(
                parse_array_event(array_event, self.allowed_telescopes)
            )
            self._add_monitoring(self.current_event)
            if self._current_calib_pe is not None:
                self.current_event["photoelectrons"] = self._current_calib_pe
                self._current_calib_pe = None

        elif isinstance(o, CalibrationPhotoelectrons):
            telescope_data = next(o)
            if not isinstance(telescope_data, iact.TelescopeData):
                warnings.warn(
                    f"Unexpected sub-object: {telescope_data} in {o}, ignoring",
                    UnknownObjectWarning
                )
                return

            self._current_calib_pe = {}
            for photoelectrons in telescope_data:
                if not isinstance(photoelectrons, iact.PhotoElectrons):
                    warnings.warn(
                        f"Unexpected sub-object: {photoelectrons} in {telescope_data}, ignoring",
                        UnknownObjectWarning
                    )

                tel_id = photoelectrons.telescope_id
                self._current_calib_pe[tel_id] = photoelectrons.parse()

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

            # file is over, assign last event
            event = self.current_event
            self.current_event = None
            self._finished = True

        elif isinstance(o, iact.AtmosphericProfile):
            self.atmospheric_profiles.append(o.parse())
        else:
            warnings.warn(
                'encountered object of type "{}" which is not handled'
                ' at the moment'.format(o),
                UnknownObjectWarning,
            )

        return event

    def _add_monitoring(self, event):
        '''check if all necessary info for an event was found,
        then make an event and invalidate old data
        '''
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

    event = {
        "event_id": event_id,
        "trigger_information": None,
        "telescope_events": telescope_events,
        "tracking_positions": tracking_positions,
    }

    for i, o in enumerate(array_event):
        # require first element to be a TriggerInformation
        if i == 0:
            check_type(o, TriggerInformation)
            # extracted calibration events seem to have a valid event id in the array event
            # but not in the trigger
            if o.header.id != 0:
                event["event_id"] = o.header.id
            trigger_information = o.parse()
            event["trigger_information"] = trigger_information
            telescopes = set(trigger_information['telescopes_with_data'])

            if allowed_telescopes and len(telescopes & allowed_telescopes) == 0:
                break

        elif isinstance(o, TelescopeEvent):
            if allowed_telescopes is None or o.telescope_id in allowed_telescopes:
                telescope_events[o.telescope_id] = parse_telescope_event(o)

        elif isinstance(o, TrackingPosition):
            if allowed_telescopes is None or o.telescope_id in allowed_telescopes:
                tracking_positions[o.telescope_id] = o.parse()
        elif isinstance(o, StereoReconstruction):
            event["stereo_reconstruction"] = o.parse()

    missing_tracking = set(telescope_events.keys()) - set(tracking_positions.keys())
    if missing_tracking:
        raise NoTrackingPositions(
            'Missing tracking positions for telescopes {}'.format(
                missing_tracking
            )
        )

    return event


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
        elif isinstance(o, (AuxiliaryAnalogTraces, AuxiliaryDigitalTraces)):
            if "aux_traces" not in event:
                event["aux_traces"] = {}
            event["aux_traces"][o.header.id] = o.parse()

    return event
