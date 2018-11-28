''' Implementations of the simtel_array EventIO object types '''
import numpy as np
from ..base import EventIOObject
from ..tools import (
    read_ints,
    read_eventio_string,
    read_from,
    read_utf8_like_signed_int,
    read_array
)


class TelescopeObject(EventIOObject):
    '''
    BaseClass that reads telescope id from header.id and puts it in repr
    '''

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def __repr__(self):
        return '{}[{}](telescope_id={}, size={}, first_byte={})'.format(
            self.__class__.__name__,
            self.eventio_type,
            self.telescope_id,
            self.header.length,
            self.header.data_field_first_byte
        )

def assert_exact_version(self, supported_version):
    if self.header.version != supported_version:
        raise IOError(
            (
                'Unsupported version of {name}'
                'only supports version {supported_version}'
                'the given version is {given_version}'
            ).format(
                name=self.__class__.__name__,
                supported_version=supported_version,
                given_version=self.header.version,
            )
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
    from .runheader_dtypes import (
        runheader_dtype_part1,
        runheader_dtype_part2
    )

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.run_id = self.header.id

    def parse_data_field(self):
        '''See write_hess_runheader l. 184 io_hess.c '''
        self.seek(0)
        dt1 = SimTelRunHeader.runheader_dtype_part1

        part1 = read_array(self, dtype=dt1, count=1)[0]
        dt2 = SimTelRunHeader.runheader_dtype_part2(part1['n_telescopes'])
        part2 = read_array(self, dtype=dt2, count=1)[0]

        # rest is two null-terminated strings
        target = read_eventio_string(self)
        observer = read_eventio_string(self)

        result = dict(zip(part1.dtype.names, part1))
        result.update(dict(zip(part2.dtype.names, part2)))
        result['target'] = target
        result['observer'] = observer

        return result


class SimTelMCRunHeader(EventIOObject):
    eventio_type = 2001
    from .mc_runheader_dtypes import mc_runheader_dtype_map

    def parse_data_field(self):
        ''' '''
        self.seek(0)

        if self.header.version not in self.mc_runheader_dtype_map:
            raise IOError(
                'Unsupported version of MCRunHeader: {}'.format(self.header.version)
            )

        header_type = self.mc_runheader_dtype_map[self.header.version]
        return read_array(self, dtype=header_type, count=1).view(np.recarray)[0]


class SimTelCamSettings(TelescopeObject):
    eventio_type = 2002

    def parse_data_field(self):
        n_pixels, = read_from('<i', self)
        focal_length, = read_from('<f', self)
        pixel_x = read_array(self, count=n_pixels, dtype='float32')
        pixel_y = read_array(self, count=n_pixels, dtype='float32')

        return {
            'telescope_id': self.telescope_id,
            'n_pixels': n_pixels,
            'focal_length': focal_length,
            'pixel_x': pixel_x,
            'pixel_y': pixel_y,
        }


class SimTelCamOrgan(EventIOObject):
    eventio_type = 2003


class SimTelPixelset(TelescopeObject):
    eventio_type = 2004
    from .pixelset import dt1, dt2, dt3, dt4

    def parse_data_field(self):
        ''' '''
        self.seek(0)

        p1 = read_array(self, dtype=SimTelPixelset.dt1, count=1)[0]

        dt2 = SimTelPixelset.dt2(num_pixels=p1['num_pixels'])
        p2 = read_array(self, dtype=dt2, count=1)[0]

        dt3 = SimTelPixelset.dt3(num_drawers=p2['num_drawers'])
        p3 = read_array(self, dtype=dt3, count=1)[0]

        nrefshape = read_utf8_like_signed_int(self)
        lrefshape = read_utf8_like_signed_int(self)

        dt4 = SimTelPixelset.dt4(nrefshape, lrefshape)
        p4 = read_array(self, dtype=dt4, count=1)[0]

        return merge_structured_arrays_into_dict([p1, p2, p3, p4])


class SimTelPixelDisable(EventIOObject):
    eventio_type = 2005

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def parse_data_field(self):
        ''' '''
        self.seek(0)

        assert_exact_version(self, supported_version=0)

        num_trig_disabled, = read_from('<i', self)
        trigger_disabled = read_array(
            self,
            count=num_trig_disabled,
            dtype='i4'
        )
        num_HV_disabled, = read_from('<i', self)
        HV_disabled = read_array(self, count=num_trig_disabled, dtype='i4')

        return {
            'telescope_id': self.telescope_id,
            'num_trig_disabled': num_trig_disabled,
            'trigger_disabled': trigger_disabled,
            'num_HV_disabled': num_HV_disabled,
            'HV_disabled': HV_disabled,
        }

class SimTelCamsoftset(EventIOObject):
    eventio_type = 2006

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def parse_data_field(self):
        ''' '''
        self.seek(0)
        assert_exact_version(self, supported_version=0)

        dyn_trig_mode, = read_from('<i', self)
        dyn_trig_threshold, = read_from('<i', self)
        dyn_HV_mode, = read_from('<i', self)
        dyn_HV_threshold, = read_from('<i', self)
        data_red_mode, = read_from('<i', self)
        zero_sup_mode, = read_from('<i', self)
        zero_sup_num_thr, = read_from('<i', self)
        zero_sup_thresholds = read_array(self, 'i4', zero_sup_num_thr)
        unbiased_scale, = read_from('<i', self)
        dyn_ped_mode, = read_from('<i', self)
        dyn_ped_events, = read_from('<i', self)
        dyn_ped_period, = read_from('<i', self)
        monitor_cur_period, = read_from('<i', self)
        report_cur_period, = read_from('<i', self)
        monitor_HV_period, = read_from('<i', self)
        report_HV_period, = read_from('<i', self)

        return {
            'telescope_id': self.telescope_id,
            'dyn_trig_mode': dyn_trig_mode,
            'dyn_trig_threshold': dyn_trig_threshold,
            'dyn_HV_mode': dyn_HV_mode,
            'dyn_HV_threshold': dyn_HV_threshold,
            'data_red_mode': data_red_mode,
            'zero_sup_mode': zero_sup_mode,
            'zero_sup_num_thr': zero_sup_num_thr,
            'zero_sup_thresholds': zero_sup_thresholds,
            'unbiased_scale': unbiased_scale,
            'dyn_ped_mode': dyn_ped_mode,
            'dyn_ped_events': dyn_ped_events,
            'dyn_ped_period': dyn_ped_period,
            'monitor_cur_period': monitor_cur_period,
            'report_cur_period': report_cur_period,
            'monitor_HV_period': monitor_HV_period,
            'report_HV_period': report_HV_period,
        }


class SimTelPointingCor(TelescopeObject):
    eventio_type = 2007

    def parse_data_field(self):
        ''' '''
        self.seek(0)
        assert_exact_version(self, supported_version=0)

        function_type, = read_from('<i', self)
        num_param, = read_from('<i', self)
        pointing_param = read_array(self, 'f4', num_param)

        return {
            'telescope_id': self.telescope_id,
            'function_type': function_type,
            'num_param': num_param,
            'pointing_param': pointing_param,
        }


class SimTelTrackSet(EventIOObject):
    eventio_type = 2008


class SimTelCentEvent(EventIOObject):
    eventio_type = 2009


class SimTelTrackEvent(EventIOObject):
    '''Tracking information for a simtel telescope event
    This has no clear type number, since
    Konrad Bernlöhr decided to encode the telescope id into
    the container type as 2100 + tel_id % 100 + 1000 * (tel_id // 100)

    So a container with type 2105 belongs to tel_id 5, 3105 to 105
    '''
    eventio_type = None

    def __init__(self, header, parent):
        self.eventio_type = header.type
        super().__init__(header, parent)
        self.telescope_id = self.type_to_telid(header.type)
        if not self.id_to_telid(header.id) == self.telescope_id:
            raise ValueError('Telescope IDs in type and header do not match')

        self.has_raw = bool(header.id & 0x100)
        self.has_cor = bool(header.id & 0x200)

    def parse_data_field(self):
        dt = []
        if self.has_raw:
            dt.extend([('azimuth_raw', '<f4'), ('altitude_raw', '<f4')])
        if self.has_cor:
            dt.extend([('azimuth_cor', '<f4'), ('altitude_cor', '<f4')])
        return read_array(self, count=1, dtype=dt)[0]

    @staticmethod
    def id_to_telid(eventio_id):
        '''See io_hess.c, l. 2519'''
        return (eventio_id & 0xff) | ((eventio_id & 0x3f000000) >> 16)

    @staticmethod
    def type_to_telid(eventio_type):
        base = eventio_type - 2100
        return 100 * (base // 1000) + base % 1000

    @staticmethod
    def telid_to_type(telescope_id):
        return 2100 + telescope_id % 100 + 1000 * (telescope_id // 100)

    def __repr__(self):
        return '{}[{}](telescope_id={}, size={}, first_byte={})'.format(
            self.__class__.__name__,
            self.eventio_type,
            self.telescope_id,
            self.header.length,
            self.header.data_field_first_byte
        )


class SimTelTelEvent(EventIOObject):
    '''A simtel telescope event
    This has no clear type number, since
    Konrad Bernlöhr decided to encode the telescope id into
    the container type as 2200 + tel_id % 100 + 1000 * (tel_id // 100)

    So a container with type 2205 belongs to tel_id 5, 3205 to 105
    '''
    eventio_type = None

    def __init__(self, header, parent):
        self.eventio_type = header.type
        super().__init__(header, parent)
        self.telescope_id = self.type_to_telid(header.type)
        self.global_count = header.id

    @staticmethod
    def type_to_telid(eventio_type):
        base = eventio_type - 2200
        return 100 * (base // 1000) + base % 1000

    @staticmethod
    def telid_to_type(telescope_id):
        return 2200 + telescope_id % 100 + 1000 * (telescope_id // 100)

    def __repr__(self):
        return '{}[{}](telescope_id={}, size={}, first_byte={})'.format(
            self.__class__.__name__,
            self.eventio_type,
            self.telescope_id,
            self.header.length,
            self.header.data_field_first_byte
        )


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

    def parse_data_field(self):
        ''' '''
        self.seek(0)
        #assert_exact_version(self, supported_version=1)

        return {
            'event': self.header.id,
            'shower_num': read_from('<i', self)[0],
            'xcore': read_from('<f', self)[0],
            'ycore': read_from('<f', self)[0],
            # 'aweight': read_from('<f', self),  # only in version 2
        }

class SimTelTelMoni(EventIOObject):
    eventio_type = 2022

    def parse_data_field(self):
        self.seek(0)
        # assert_exact_version(self, supported_version=0)

        telescope_id = (
            (self.header.id & 0xff) |
            ((self.header.id & 0x3f000000) >> 16)
        )

        # what: denotes what has changed (since last report?)
        what = ((self.header.id & 0xffff00) >> 8) & 0xffff
        known, = read_from('<h', self)   # C-code used |= instead of = here.
        new_parts, = read_from('<h', self)
        monitor_id, = read_from('<i', self)
        moni_time = read_time(self)

        #  Dimensions of various things
        # version 0
        ns, np, nd, ng = read_from('<hhhh', self)
        # in version 1 this uses crazy 32bit ints
        # ns = read_utf8_like_signed_int(self)
        # np = read_utf8_like_signed_int(self)
        # nd = read_utf8_like_signed_int(self)
        # ng = read_utf8_like_signed_int(self)

        part_parser_args = {
            'num_sectors': ns,
            'num_gains': ng,
            'num_pixels': np,
            'num_drawers': nd,
        }
        result = {
            'telescope_id': telescope_id,
            'what': what,
            'known': known,
            'new_parts': new_parts,
            'monitor_id': monitor_id,
            'moni_time': moni_time,
        }.update(part_parser_args)

        part_parser_map = {
            0x00: self._nothing_changed_here,
            0x01: self._status_only_changed__what_and_0x01,
            0x02: self._counts_and_rates_changed__what_and_0x02,
            0x04: self._pedestal_and_noice_changed__what_and_0x04,
            0x08: self._HV_and_temp_changed__what_and_0x08,
            0x10: self._pixel_scalers_DC_i_changed__what_and_0x10,
            0x20: self._HV_thresholds_changed__what_and_0x20,
            0x40: self._DAQ_config_changed__what_and_0x40,
        }

        result = {}
        for part_id in range(8):
            part_parser = part_parser_map[what & (1 << part_id)]
            result.update(part_parser(**part_parser_args))
        return result

    def _nothing_changed_here(self, **kwargs):
        ''' dummy parser, invoked when this bit is not set '''
        return {}

    def _status_only_changed__what_and_0x01(self, **kwargs):
        return {
            'status_time': read_time(self),
            'status_bits': read_from('<i', self)[0],
        }

    def _counts_and_rates_changed__what_and_0x02(self, num_sectors, **kwargs):
        return {
            'trig_time': read_time(self),
            'coinc_count': read_from('<l', self)[0],
            'event_count': read_from('<l', self)[0],
            'trigger_rate': read_from('<f', self)[0],
            'sector_rate': read_array(self, 'f4', num_sectors),
            'event_rate': read_from('<f', self)[0],
            'data_rate': read_from('<f', self)[0],
            'mean_significant': read_from('<f', self)[0],
        }

    def _pedestal_and_noice_changed__what_and_0x04(self, num_gains, num_pixels, **kwargs):
        return {
            'ped_noise_time': read_time(self),
            'num_ped_slices': read_from('<h', self)[0],
            'pedestal': read_array(
                self, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
            'noise': read_array(
                self, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
        }

    def _HV_and_temp_changed__what_and_0x08(self, num_pixels, num_drawers, **kwargs):
        hv_temp_time = read_time(self),
        num_drawer_temp = read_from('<h', self)[0]
        num_camera_temp = read_from('<h', self)[0]
        return {
            'hv_temp_time': hv_temp_time,
            'num_drawer_temp': num_drawer_temp,
            'num_camera_temp': num_camera_temp,
            'hv_v_mon': read_array(self, 'i2', num_pixels),
            'hv_i_mon': read_array(self, 'i2', num_pixels),
            'hv_stat': read_array(self, 'B', num_pixels),
            'drawer_temp': read_array(
                self, 'i2', num_drawers * num_drawer_temp
            ).reshape((num_drawers, num_drawer_temp)),
            'camera_temp': read_array(self, 'i2', num_camera_temp),
        }

    def _pixel_scalers_DC_i_changed__what_and_0x10(self, num_pixels, **kwargs):
        return {
            'dc_rate_time': read_time(self),
            'current': read_array(self, 'u2', num_pixels),
            'scaler': read_array(self, 'u2', num_pixels),
        }

    def _HV_thresholds_changed__what_and_0x20(self, num_pixels, num_drawers,  **kwargs):
        return {
            'hv_thr_time': read_time(self),
            'hv_dac': read_array(self, 'u2', num_pixels),
            'thresh_dac': read_array(self, 'u2', num_drawers),
            'hv_set': read_array(self, 'B', num_pixels),
            'trig_set': read_array(self, 'B', num_pixels),
        }

    def _DAQ_config_changed__what_and_0x40(self, **kwargs):
        return {
            'set_daq_time': read_time(self),
            'daq_conf': read_from('<H', self)[0],
            'daq_scaler_win': read_from('<H', self)[0],
            'daq_nd': read_from('<H', self)[0],
            'daq_acc': read_from('<H', self)[0],
            'daq_nl': read_from('<H', self)[0],
        }


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
