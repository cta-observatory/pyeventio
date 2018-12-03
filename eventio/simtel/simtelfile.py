"""
    RunHeader[2000]
    MCRunHeader[2001]
    CORSIKAInputCard[1212]

        # 1x per telescope (n_telescopes is in RunHeader)
        # I call this TelescopeDescription
    {
        SimTelCamSettings[2002]
        SimTelCamOrgan[2003]
        SimTelPixelset[2004]
        SimTelPixelDisable[2005]
        SimTelCamsoftset[2006]
        SimTelTrackSet[2008]
        SimTelPointingCor[2007]
    }

    {
        MCShower[2020](shower=3)
        {
            MCEvent[2021](event=301)
            CORSIKATelescopeData[1204](event=301)
                # IACTPhotoElectrons inside

            { 1x per telescope and I don't know why they come here
            TelMoni[2022](telescope_id=1, what=0x7f)
            LasCal[2023](telescope_id=1)
            }
            MCPeSum[2026](id=301)
            Event[2010]
            {
                CentEvent[2009](id=301)
                TelEvent[2229](telescope_id=29, id=301)
                {
                    TelEvtHead[2011](telescope_id=29)
                    TelADCSamp[2013](telescope_id=29,
                    PixelTiming[2016](telescope_id=29)
                    TelImage[2014](telescope_id=29,
                    PixelList[2027](telescope_id=29
                }
                TelEvent[2237](telescope_id=37, id=301)
                TrackEvent[2113](telescope_id=13
                TrackEvent[2117](telescope_id=17
                TrackEvent[2123](telescope_id=23
                TrackEvent[2129](telescope_id=29
                TrackEvent[2131](telescope_id=31
                ...
                TrackEvent[2163](telescope_id=63
                Shower[2015]
            }
        }


    }


"""
from eventio.base import EventIOFile, EventIOObject

class WrongType(Exception):
    pass


class WithNextAssert:
    '''MixIn for EventIoFile adding `next_assert`'''

    def next_assert(self, object_):
        '''return next object from file, only
        if it is of type `object_`
        else raise WrongType

        Make sure the object is not lost, but another call to next_assert
        will see the exact same object
        '''
        if not hasattr(self, '_last_obj'):
            self._last_obj = None

        if self._last_obj is None:
            try:
                self._last_obj = next(self)
            except StopIteration:
                raise WrongType

        o = self._last_obj
        if not isinstance(o, object_):
            raise WrongType(f"is:{o}, not:{object_}")

        self._last_obj = None
        return o

    def next_type_or_none(self, object_):
        '''return next object from file, only
        if it is of type `object_`
        else return None

        Make sure the object is not lost, but another call to next_assert
        will see the exact same object
        '''
        if not hasattr(self, '_last_obj'):
            self._last_obj = None

        if self._last_obj is None:
            try:
                self._last_obj = next(self)
            except StopIteration:
                raise WrongType

        o = self._last_obj

        if not isinstance(o, object_):
            return None

        self._last_obj = None
        return o


EventIOObject.next_assert = WithNextAssert.next_assert
EventIOObject.next_type_or_none = WithNextAssert.next_type_or_none

from eventio.iact.objects import CORSIKAInputCard, CORSIKATelescopeData
from eventio.simtel.objects import (
    History,
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


class SimTelFile:
    def __init__(self, path):
        self.path = path
        self.file_ = EventIOFileWithNextAssert(path)

        self.history = []
        while True:
            try:
                self.history.append(self.file_.next_assert(History))
            except WrongType:
                break

        self.header = self.file_.next_assert(SimTelRunHeader)
        self.n_telescopes = self.header.parse_data_field()['n_telescopes']
        self.mc_header = read_all_of_type(self.file_, SimTelMCRunHeader)
        self.corsika_input = read_all_of_type(self.file_, CORSIKAInputCard)
        self.telescope_descriptions = [
            telescope_description_from(self.file_)
            for _ in range(self.n_telescopes)
        ]

        self.shower = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            shower, event = self.fetch_next_event()
            if 'event' in event:
                return shower, event

    def fetch_next_event(self):
        try:
            event = self.next_mc_event()
            return self.shower, event
        except WrongType:
            try:
                self.shower = self.file_.next_assert(SimTelMCShower)
            except WrongType:
                raise StopIteration

            event = self.next_mc_event()
            return self.shower, event

    def next_mc_event(self):
        result = {}

        # There is for sure exactly one of these
        result['mc_event'] = self.file_.next_assert(SimTelMCEvent)
        result['corsika_tel_data'] = self.file_.next_type_or_none(CORSIKATelescopeData)

        self.moni_lascal = try_to_read_moni_lascal(self.file_, self.n_telescopes)
        try:
            result['pe_sum'] = self.file_.next_assert(SimTelMCPeSum)
        except WrongType:
            return result

        # iff we had a MCPeSum we also must have an Event
        event_ = self.file_.next_assert(SimTelEvent)
        result['event'] = parse_event(event_)

        return result





def try_to_read_moni_lascal(f, n_telescopes):
    try:
        return [
            (
                f.next_assert(SimTelTelMoni),
                f.next_assert(SimTelLasCal),
            )
            for _ in range(n_telescopes)
        ]
    except WrongType:
        pass


class EventIOFileWithNextAssert(EventIOFile, WithNextAssert):
    pass


def telescope_description_from(file_):
    return [
        file_.next_assert(SimTelCamSettings),
        file_.next_assert(SimTelCamOrgan),
        file_.next_assert(SimTelPixelset),
        file_.next_assert(SimTelPixelDisable),
        file_.next_assert(SimTelCamsoftset),
        file_.next_assert(SimTelTrackSet),
        file_.next_assert(SimTelPointingCor),
    ]


def read_all_of_type(f, type_, converter=lambda x: x):
    result = []
    while True:
        try:
            result.append(
                converter(
                    f.next_assert(type_)
                )
            )
        except WrongType:
            break
    return result


def parse_event(event):
    '''structure of event:
        CentEvent[2009]  <-- this knows how many TelEvents

        TelEvent[2202]
        ...
        TelEvent[2208]

        TrackEvent[2101]
        ...
        TrackEvent[2164]

        Shower[2015]


        In words:
            1 cent event
            n tel events
            m track events (n does not need to be == m)
            1 shower
    '''
    result = {}
    result['cent_event'] = event.next_assert(SimTelCentEvent)
    result['tel_events'] = read_all_of_type(
        event,
        SimTelTelEvent,
        converter=parse_tel_event,
    )
    #assert result['tel_events'], (result, result['cent_event'].header)  # more than zero
    result['track_events'] = read_all_of_type(event, SimTelTrackEvent)
    #assert result['track_events'], (result, result['cent_event'].header)  # more than zero
    result['shower'] = read_all_of_type(event, SimTelShower)
    return result


def parse_tel_event(tel_event):
    '''structure of tel_event
    probably: did survive cleaning and hence we have shower information
     SimTelTelEvent[2204]
         SimTelTelEvtHead[2011]
         SimTelTelADCSamp[2013]
         SimTelPixelTiming[2016]
         SimTelTelImage[2014]
         SimTelPixelList[2027]

    probably: did not survive cleaning
     SimTelTelEvent[2208]
         SimTelTelEvtHead[2011]
         SimTelTelADCSamp[2013]
         SimTelPixelTiming[2016]
    '''

    # These 3 are sure
    header = tel_event.next_assert(SimTelTelEvtHead)

    # well could be either ADCSamp or ADCSum
    adc_stuff = tel_event.next_type_or_none(SimTelTelADCSamp)
    if adc_stuff is None:
        adc_stuff = tel_event.next_type_or_none(SimTelTelADCSum)
        if adc_stuff is None:
            raise WrongType
    waveform = adc_stuff.parse_data_field()
    pixel_timing = tel_event.next_assert(SimTelPixelTiming)
    result = {
        'header': header,
        'waveform': waveform,
        'pixel_timing': pixel_timing,
    }

    # these are only sometimes there

    image = tel_event.next_type_or_none(SimTelTelImage)
    if image is not None:
        result['image'] = image
    result['pixel_list'] = tel_event.next_type_or_none(SimTelPixelList)

    return result
