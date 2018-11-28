''' Methods to read in and parse the simtel_array EventIO object types '''
import numpy as np
from ..base import EventIOObject
from ..tools import (
    read_ints,
    read_eventio_string,
    read_utf8_like_signed_int_from_bytes
)


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
    from .mc_runheader_dtypes import mc_runheader_dtype_map

    def parse_data_field(self):
        ''' '''
        self.seek(0)
        data = self.read()

        if self.header.version not in self.mc_runheader_dtype_map:
            raise IOError(
                'Unsupported version of MCRunHeader: {}'.format(self.header.version)
            )

        header_type = self.mc_runheader_dtype_map[self.header.version]
        return np.frombuffer(
            data,
            dtype=header_type,
            count=1,
            offset=0,
        ).view(np.recarray)[0]


class SimTelCamSettings(EventIOObject):
    eventio_type = 2002


class SimTelCamOrgan(EventIOObject):
    eventio_type = 2003


class SimTelPixelset(EventIOObject):
    eventio_type = 2004
    from .pixelset import dt1, dt2, dt3, dt4

    def parse_data_field(self):
        ''' '''
        self.seek(0)
        data = self.read()

        # each block below consumes the amount of bytes from `data`
        # which is needed by that block.
        # in the end `data` should either be empty or contain only a few
        # trailing zero-bytes (In my tests I saw one zero byte in the end)

        p1 = np.frombuffer(data, dtype=SimTelPixelset.dt1, count=1)[0]
        data = data[SimTelPixelset.dt1.itemsize:]

        dt2 = SimTelPixelset.dt2(num_pixels=p1['num_pixels'])
        p2 = np.frombuffer(data, dtype=dt2, count=1)[0]
        data = data[dt2.itemsize:]

        dt3 = SimTelPixelset.dt3(num_drawers=p2['num_drawers'])
        p3 = np.frombuffer(data, dtype=dt3, count=1)[0]
        data = data[dt3.itemsize:]

        nrefshape, data = read_utf8_like_signed_int_from_bytes(data)
        lrefshape, data = read_utf8_like_signed_int_from_bytes(data)

        dt4 = SimTelPixelset.dt4(nrefshape, lrefshape)
        p4 = np.frombuffer(data, dtype=dt4, count=1)
        data = data[dt4.itemsize:]

        return merge_structured_arrays_into_dict([p1, p2, p3, p4])


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


def merge_structured_arrays_into_dict(arrays):
    result = dict()
    for array in arrays:
        for name in array.dtype.names:
            result[name] = array[name]
    return result
