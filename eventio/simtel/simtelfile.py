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
from eventio.base import EventIOFile
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
        self.file_ = EventIOFile(path)

        self.history = next_assert(self.file_, History)
        self.header = next_assert(self.file_, SimTelRunHeader)
        self.mc_header = next_assert(self.file_, SimTelMCRunHeader)
        self.corsika_input = next_assert(self.file_, CORSIKAInputCard)

        self.n_telescopes = self.header.parse_data_field()['n_telescopes']
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
        except AssertionError:
            try:
                self.shower = next_assert(self.file_, SimTelMCShower)
                event = self.next_mc_event()
                return self.shower, event
            except AssertionError:
                raise StopIteration

    def next_mc_event(self):
        result = {}
        result['mc_event'] = next_assert(self.file_, SimTelMCEvent)
        try:
            result['corsika_tel_data'] = next_assert(self.file_, CORSIKATelescopeData)
        except AssertionError:
            pass

        try:
            result['moni_lascal'] = [
                (
                    next_assert(self.file_, SimTelTelMoni),
                    next_assert(self.file_, SimTelLasCal),
                )
                for _ in range(self.n_telescopes)
            ]
        except AssertionError:
            pass

        try:
            result['pe_sum'] = next_assert(self.file_, SimTelMCPeSum)
            result['event'] = next_assert(self.file_, SimTelEvent)
        except AssertionError:
            pass

        return result


def telescope_description_from(file_):
    return [
        next_assert(file_, SimTelCamSettings),
        next_assert(file_, SimTelCamOrgan),
        next_assert(file_, SimTelPixelset),
        next_assert(file_, SimTelPixelDisable),
        next_assert(file_, SimTelCamsoftset),
        next_assert(file_, SimTelTrackSet),
        next_assert(file_, SimTelPointingCor),
    ]


__last_obj = None

def next_assert(file_, object_):
    global __last_obj

    if __last_obj is None:
        __last_obj = next(file_)

    o = __last_obj

    assert isinstance(o, object_), f"is:{o}, not:{object_}"

    __last_obj = None
    return o
