''' Methods to read in and parse the simtel_array EventIO object types '''
import numpy as np
from ..base import EventIOObject
from ..tools import read_ints, read_eventio_string, read_from, read_time


class History(EventIOObject):
    eventio_type = 70


class HistoryCommandLine(EventIOObject):
    eventio_type = 71

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.timestamp, = read_ints(1, self)

    def parse_data_field(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class HistoryConfig(EventIOObject):
    eventio_type = 72

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.timestamp, = read_ints(1, self)

    def parse_data_field(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class SimTelRunHeader(EventIOObject):
    eventio_type = 2000


class SimTelMCRunHeader(EventIOObject):
    eventio_type = 2001


class SimTelCamSettings(EventIOObject):
    eventio_type = 2002


class SimTelCamOrgan(EventIOObject):
    eventio_type = 2003


class SimTelPixelset(EventIOObject):
    eventio_type = 2004


class SimTelPixelDisable(EventIOObject):
    eventio_type = 2005


class SimTelCamsoftset(EventIOObject):
    eventio_type = 2006


class SimTelPointingCor(EventIOObject):
    eventio_type = 2007


class SimTelTrackSet(EventIOObject):
    eventio_type = 2008


class SimTelCentEvent(EventIOObject):
    eventio_type = 2009

    def __init__(self, header, parent):
        super().__init__(header, parent)

        if header.version > 2:
            raise IOError('Unsupported CENTEVENT Version: {}'.format(header.version))

        self.global_count = self.header.id

    def parse_data_field(self):

        event_info = {}
        event_info['cpu_time'] = read_time(self)
        event_info[']gps_time'] = read_time(self)
        event_info['trigger_pattern'], = read_from('<i', self)
        event_info['data_pattern'], = read_from('<i', self)

        if self.header.version >= 1:
            tels_trigger, = read_from('<h', self)
            print(tels_trigger)
            event_info['n_triggered_telescopes'] = tels_trigger

            event_info['triggered_telescopes'] = np.frombuffer(
                self.read(tels_trigger * 2), dtype='<i2',
            )
            event_info['trigger_times'] = np.frombuffer(
                self.read(tels_trigger * 4), dtype='<f4',
            )
            tels_data, = read_from('<h', self)
            event_info['n_telescopes_with_data'] = tels_data
            event_info['telescopes_with_data'] = np.frombuffer(
                self.read(tels_data * 2), dtype='<i2'
            )

        # TODO: read telttrg_type_mask

        return event_info


class SimTelTrackEvent(EventIOObject):
    eventio_type = 2100


class SimTelTelEvent(EventIOObject):
    eventio_type = 2200


class SimTelEvent(EventIOObject):
    eventio_type = 2010


class SimTelTelEvtHead(EventIOObject):
    eventio_type = 2011


class SimTelTelADCSum(EventIOObject):
    eventio_type = 2012


class SimTelTelADCSamp(EventIOObject):
    eventio_type = 2013


class SimTelTelImage(EventIOObject):
    eventio_type = 2014


class SimTelShower(EventIOObject):
    eventio_type = 2015


class SimTelPixelTiming(EventIOObject):
    eventio_type = 2016


class SimTelPixelCalib(EventIOObject):
    eventio_type = 2017


class SimTelMCShower(EventIOObject):
    eventio_type = 2020


class SimTelMCEvent(EventIOObject):
    eventio_type = 2021


class SimTelTelMoni(EventIOObject):
    eventio_type = 2022


class SimTelLasCal(EventIOObject):
    eventio_type = 2023


class SimTelRunStat(EventIOObject):
    eventio_type = 2024


class SimTelMCRunStat(EventIOObject):
    eventio_type = 2025


class SimTelMCPeSum(EventIOObject):
    eventio_type = 2026


class SimTelPixelList(EventIOObject):
    eventio_type = 2027


class SimTelCalibEvent(EventIOObject):
    eventio_type = 2028
