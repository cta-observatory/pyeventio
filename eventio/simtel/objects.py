''' Implementations of the simtel_array EventIO object types '''
import numpy as np
import struct
from ..base import EventIOObject, read_next_header
from ..tools import (
    read_short,
    read_int,
    read_float,
    read_eventio_string,
    read_from,
    read_utf8_like_signed_int,
    read_utf8_like_unsigned_int,
    read_array,
    read_time,
)
from ..bits import bool_bit_from_pos
from ..var_int import (
    unsigned_varint_arrays_differential,
    unsigned_varint_array,
    varint_array,
    unsigned_varint,
    varint,
)
from ..version_handling import (
    assert_exact_version,
    assert_max_version,
    assert_version_in
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


class History(EventIOObject):
    eventio_type = 70


class HistoryCommandLine(EventIOObject):
    eventio_type = 71

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.timestamp = read_int(self)

    def parse_data_field(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class HistoryConfig(EventIOObject):
    eventio_type = 72

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.timestamp = read_int(self)

    def parse_data_field(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class SimTelRunHeader(EventIOObject):
    eventio_type = 2000
    from .runheader_dtypes import (
        build_dtype_part1,
        build_dtype_part2
    )

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.run_id = self.header.id

    def parse_data_field(self):
        '''See write_hess_runheader l. 184 io_hess.c '''
        assert_max_version(self, 2)

        self.seek(0)
        dt1 = SimTelRunHeader.build_dtype_part1(self.header.version)

        part1 = read_array(self, dtype=dt1, count=1)[0]
        dt2 = SimTelRunHeader.build_dtype_part2(
            self.header.version,
            part1['n_telescopes']
        )
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

    def parse_data_field(self):
        assert_exact_version(self, 4)
        self.seek(0)

        return {
            'shower_prog_id': read_int(self),
            'shower_prog_vers': read_int(self),
            'shower_prog_start': read_int(self),
            'detector_prog_id': read_int(self),
            'detector_prog_vers': read_int(self),
            'detector_prog_start': read_int(self),
            'obsheight': read_float(self),
            'num_showers': read_int(self),
            'num_use': read_int(self),
            'core_pos_mode': read_int(self),
            'core_range': read_array(self, 'f4', 2),
            'alt_range': read_array(self, 'f4', 2),
            'az_range': read_array(self, 'f4', 2),
            'diffuse': read_int(self),
            'viewcone': read_array(self, 'f4', 2),
            'E_range': read_array(self, 'f4', 2),
            'spectral_index': read_float(self),
            'B_total': read_float(self),
            'B_inclination': read_float(self),
            'B_declination': read_float(self),
            'injection_height': read_float(self),
            'atmosphere': read_int(self),
            'corsika_iact_options': read_int(self),
            'corsika_low_E_model': read_int(self),
            'corsika_high_E_model': read_int(self),
            'corsika_bunchsize': read_float(self),
            'corsika_wlen_min': read_float(self),
            'corsika_wlen_max': read_float(self),
            'corsika_low_E_detail': read_int(self),
            'corsika_high_E_detail': read_int(self),
        }


class SimTelCamSettings(TelescopeObject):
    eventio_type = 2002

    def parse_data_field(self):
        assert_version_in(self, [0, 1, 2, 3, 4, 5])
        self.seek(0)
        n_pixels = read_int(self)

        cam = {'n_pixels': n_pixels, 'telescope_id': self.telescope_id}
        cam['focal_length'] = read_float(self)
        if self.header.version > 4:
            cam['effective_focal_length'] = read_float(self)

        cam['pixel_x'] = read_array(self, count=n_pixels, dtype='float32')
        cam['pixel_y'] = read_array(self, count=n_pixels, dtype='float32')

        if self.header.version >= 4:
            cam['curved_surface'] = read_utf8_like_signed_int(self)
            cam['pixels_parallel'] = read_utf8_like_signed_int(self)

            if cam['curved_surface']:
                cam['pixel_z'] = read_array(self, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_z'] = np.zeros(n_pixels, dtype='<f4')

            if not cam['pixels_parallel']:
                cam['nxpix'] = read_array(self, dtype='<f4', count=n_pixels)
                cam['nypix'] = read_array(self, dtype='<f4', count=n_pixels)
            else:
                cam['nxpix'] = cam['nypix'] = np.zeros(n_pixels, dtype='f4')

            cam['common_pixel_shape'] = read_utf8_like_signed_int(self)
            if not cam['common_pixel_shape']:
                cam['pixel_shape'] = np.array([
                    read_utf8_like_signed_int(self) for _ in range(n_pixels)
                ])
                cam['pixel_area'] = read_array(self, dtype='<f4', count=n_pixels)
                cam['pixel_size'] = read_array(self, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_shape'] = np.repeat(read_utf8_like_signed_int(self), n_pixels)
                cam['pixel_area'] = np.repeat(read_float(self), n_pixels)
                cam['pixel_size'] = np.repeat(read_float(self), n_pixels)
        else:
            cam['curve_surface'] = 0
            cam['pixels_parallel'] = 1
            cam['common_pixel_shape'] = 0
            cam['pixel_z'] = np.zeros(n_pixels, dtype='f4')
            cam['nxpix'] = cam['nypix'] = np.zeros(n_pixels, dtype='f4')
            cam['pixel_shape'] = np.full(n_pixels, -1, dtype='f4')
            cam['pixel_area'] = read_array(self, dtype='<f4', count=n_pixels)
            if self.header.version >= 1:
                cam['pixel_size'] = read_array(self, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_size'] = np.zeros(n_pixels, dtype='f4')

        if self.header.version >= 2:
            cam['n_mirrors'] = read_int(self)
            cam['mirror_area'] = read_float(self)
        else:
            cam['n_mirrors'] = 0.0
            cam['mirror_area'] = 0.0

        if self.header.version >= 3:
            cam['cam_rot'] = read_float(self)
        else:
            cam['cam_rot'] = 0.0

        return cam


class SimTelCamOrgan(TelescopeObject):
    eventio_type = 2003

    from .camorgan import read_sector_information

    def parse_data_field(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)

        num_pixels = read_int(self)
        num_drawers = read_int(self)
        num_gains = read_int(self)
        num_sectors = read_int(self)

        drawer = read_array(self, 'i2', num_pixels)
        card = read_array(
            self, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)
        chip = read_array(
            self, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)
        channel = read_array(
            self, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)

        data = self.read()
        pos = 0
        sectors, bytes_read = SimTelCamOrgan.read_sector_information(
            data, num_pixels
        )
        pos += bytes_read

        sector_data = np.frombuffer(
            data,
            dtype=[
                ('type', 'uint8'),
                ('thresh', 'float32'),
                ('pix_thresh', 'float32')
            ],
            count=num_sectors,
            offset=pos,
        )

        return {
            'telescope_id': self.telescope_id,
            'num_drawers': num_drawers,
            'drawer': drawer,
            'card': card,
            'chip': chip,
            'channel': channel,
            'sectors': sectors,
            'sector_type': sector_data['type'],
            'sector_threshold': sector_data['thresh'],
            'sector_pixthresh': sector_data['pix_thresh'],
        }


class SimTelPixelset(TelescopeObject):
    eventio_type = 2004
    from .pixelset import dt1, build_dt2, build_dt3, build_dt4

    def parse_data_field(self):
        assert_max_version(self, 2)
        self.seek(0)

        p1 = read_array(self, dtype=SimTelPixelset.dt1, count=1)[0]

        dt2 = SimTelPixelset.build_dt2(num_pixels=p1['num_pixels'])
        p2 = read_array(self, dtype=dt2, count=1)[0]

        dt3 = SimTelPixelset.build_dt3(
            self.header.version, num_drawers=p2['num_drawers']
        )
        p3 = read_array(self, dtype=dt3, count=1)[0]

        parts = [p1, p2, p3]
        if self.header.version >= 2:
            nrefshape = read_utf8_like_signed_int(self)
            lrefshape = read_utf8_like_signed_int(self)

            dt4 = SimTelPixelset.build_dt4(nrefshape, lrefshape)
            parts.append(read_array(self, dtype=dt4, count=1)[0])

        return merge_structured_arrays_into_dict(parts)


class SimTelPixelDisable(EventIOObject):
    eventio_type = 2005

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def parse_data_field(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        num_trig_disabled = read_int(self)
        trigger_disabled = read_array(
            self,
            count=num_trig_disabled,
            dtype='i4'
        )
        num_HV_disabled = read_int(self)
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
        assert_exact_version(self, supported_version=0)
        self.seek(0)

        dyn_trig_mode = read_int(self)
        dyn_trig_threshold = read_int(self)
        dyn_HV_mode = read_int(self)
        dyn_HV_threshold = read_int(self)
        data_red_mode = read_int(self)
        zero_sup_mode = read_int(self)
        zero_sup_num_thr = read_int(self)
        zero_sup_thresholds = read_array(self, 'i4', zero_sup_num_thr)
        unbiased_scale = read_int(self)
        dyn_ped_mode = read_int(self)
        dyn_ped_events = read_int(self)
        dyn_ped_period = read_int(self)
        monitor_cur_period = read_int(self)
        report_cur_period = read_int(self)
        monitor_HV_period = read_int(self)
        report_HV_period = read_int(self)

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
        assert_exact_version(self, supported_version=0)
        self.seek(0)

        function_type = read_int(self)
        num_param = read_int(self)
        pointing_param = read_array(self, 'f4', num_param)

        return {
            'telescope_id': self.telescope_id,
            'function_type': function_type,
            'num_param': num_param,
            'pointing_param': pointing_param,
        }


class SimTelTrackSet(TelescopeObject):
    eventio_type = 2008

    def parse_data_field(self):
        assert_exact_version(self, 0)
        self.seek(0)

        tracking_info = {}
        tracking_info['drive_type_az'] = read_short(self)
        tracking_info['drive_type_alt'] = read_short(self)
        tracking_info['zeropoint_az'] = read_float(self)
        tracking_info['zeropoint_alt'] = read_float(self)

        tracking_info['sign_az'] = read_float(self)
        tracking_info['sign_alt'] = read_float(self)
        tracking_info['resolution_az'] = read_float(self)
        tracking_info['resolution_alt'] = read_float(self)
        tracking_info['range_low_az'] = read_float(self)
        tracking_info['range_low_alt'] = read_float(self)
        tracking_info['range_high_az'] = read_float(self)
        tracking_info['range_high_alt'] = read_float(self)
        tracking_info['park_pos_az'] = read_float(self)
        tracking_info['park_pos_alt'] = read_float(self)

        return tracking_info


class SimTelCentEvent(EventIOObject):
    eventio_type = 2009

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.global_count = self.header.id

    def parse_data_field(self):
        assert_max_version(self, 2)
        self.seek(0)

        event_info = {}
        event_info['cpu_time'] = read_time(self)
        event_info['gps_time'] = read_time(self)
        event_info['trigger_pattern'] = read_int(self)
        event_info['data_pattern'] = read_int(self)

        if self.header.version >= 1:
            tels_trigger = read_short(self)
            event_info['n_triggered_telescopes'] = tels_trigger

            event_info['triggered_telescopes'] = read_array(
                self, count=tels_trigger, dtype='<i2',
            )
            event_info['trigger_times'] = read_array(
                self, count=tels_trigger, dtype='<f4',
            )
            tels_data = read_short(self)
            event_info['n_telescopes_with_data'] = tels_data
            event_info['telescopes_with_data'] = read_array(
                self, count=tels_data, dtype='<i2'
            )

        if self.header.version >= 2:
            # konrad saves the trigger mask as crazy int, but it uses only 4 bits
            # so it should be indentical to a normal unsigned int with 1 byte
            event_info['teltrg_type_mask'] = read_array(
                self, count=tels_trigger, dtype='uint8'
            )
            assert np.all(event_info['teltrg_type_mask'] < 128), 'Unexpected trigger mask'

            event_info['teltrg_time_by_type'] = {}
            it = zip(event_info['triggered_telescopes'], event_info['teltrg_type_mask'])
            for tel_id, mask in it:
                # trigger times are only written if more than one trigger is there
                if mask not in {0b001, 0b010, 0b100}:
                    event_info['teltrg_time_by_type'][tel_id] = {}
                    for trigger in range(3):
                        if bool_bit_from_pos(mask, trigger):
                            t = read_float(self)
                            event_info['teltrg_time_by_type'][tel_id][trigger] = t

        return event_info


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
        assert_exact_version(self, 0)

        self.seek(0)
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

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.glob_count = header.id

    def __repr__(self):
        return '{}[{}](glob_count={}, size={}, first_byte={})'.format(
            self.__class__.__name__,
            self.eventio_type,
            self.glob_count,
            self.header.length,
            self.header.data_field_first_byte
        )


class SimTelTelEvtHead(TelescopeObject):
    eventio_type = 2011

    def parse_data_field(self):
        assert_max_version(self, 2)

        self.seek(0)
        event_head = {}
        event_head['loc_count'] = read_int(self)
        event_head['glob_count'] = read_int(self)
        event_head['cpu_time'] = read_time(self)
        event_head['gps_time'] = read_time(self)
        t = read_short(self)
        event_head['trg_source'] = t & 0xff

        pos = 0
        data = self.read()

        if t & 0x100:
            if self.header.version <= 1:
                num_list_trgsect, = struct.unpack('<h', data[pos:pos + 2])
                pos += 2
                event_head['list_trgsect'] = np.frombuffer(
                    data, dtype='<i2', count=num_list_trgsect, offset=pos,
                )
                pos += num_list_trgsect * 2
            else:
                num_list_trgsect, length = varint(data, offset=pos)
                pos += length
                event_head['list_trgsect'], length = varint_array(
                    data, n_elements=num_list_trgsect, offset=pos,
                )
                pos += length
            if self.header.version >= 1 and (t & 0x400):
                event_head['time_trgsect'] = np.frombuffer(
                    data, dtype='<f4', count=num_list_trgsect, offset=pos
                )
                pos += 4 * num_list_trgsect

        if t & 0x200:
            if self.header.version <= 1:
                event_head['num_phys_addr'] = struct.unpack('<h', data[pos:pos + 2])
                pos += 2
                event_head['phys_addr'] = np.from_buffer(
                    data, dtype='<i2', count=event_head['num_phys_addr'], offset=pos
                )
                pos += 2 * event_head['num_phys_addr']
            else:
                event_head['num_phys_addr'], length = varint(data, offset=pos)
                pos += length
                event_head['phys_addr'], length = varint_array(
                    data, n_elements=event_head['num_phys_addr'], offset=pos
                )
                pos += length

        return event_head


class SimTelTelADCSum(EventIOObject):
    eventio_type = 2012

    def __init__(self, header, parent):
        super().__init__(header, parent)
        if self.header.version <= 1:
            self.telescope_id = (header.id >> 25) & 0x1f
        else:
            self.telescope_id = (header.id >> 12) & 0xffff

    def parse_data_field(self):
        assert_exact_version(self, 3)
        self.seek(0)

        flags = self.header.id
        raw = {'telescope_id': self.telescope_id}
        raw['zero_sup_mode'] = flags & 0x1f
        raw['data_red_mode'] = (flags >> 5) & 0x1f
        raw['list_known'] = (flags >> 10) & 0x01
        n_pixels = read_int(self)
        n_gains = read_short(self)

        if raw['data_red_mode'] != 0 or raw['zero_sup_mode'] != 0:
            raise NotImplementedError(
                'Currently no support for data_red_mode {} or zero_sup_mode{}'.format(
                    raw['data_red_mode'], raw['zero_sup_mode'],
                )
            )

        raw['adc_sums'] = []
        data = self.read()
        raw['adc_sums'], bytes_read = unsigned_varint_arrays_differential(
            data, n_arrays=n_gains, n_elements=n_pixels
        )

        return raw


class SimTelTelADCSamp(EventIOObject):
    eventio_type = 2013

    def __init__(self, header, parent):
        super().__init__(header, parent)
        flags_ = header.id
        self._zero_sup_mode = flags_ & 0x1f
        self._data_red_mode = (flags_ >> 5) & 0x1f
        self._list_known = bool((flags_ >> 10) & 0x01)

        #  !! WTF: raw->zero_sup_mode |= zero_sup_mode << 5

        self.telescope_id = (flags_ >> 12) & 0xffff

    def parse_data_field(self):
        assert_exact_version(self, supported_version=3)
        unsupported = (
            self._zero_sup_mode != 0
            or self._data_red_mode != 0
            or self._list_known
        )
        if unsupported:
            raise NotImplementedError

        self.seek(0)

        args = {
            'num_pixels': read_int(self),
            'num_gains': read_short(self),
            'num_samples': read_short(self),
        }
        if self._zero_sup_mode:
            return self._parse_in_zero_suppressed_mode(**args)
        else:
            return self._parse_in_not_zero_suppressed_mode(**args)

    def _parse_in_zero_suppressed_mode(
        self,
        num_gains,
        num_pixels,
        num_samples,
    ):
        list_size = read_utf8_like_signed_int(self)
        pixel_ranges = []
        for _ in range(list_size):
            start_pixel_id = read_utf8_like_signed_int(self)
            if start_pixel_id < 0:
                pixel_ranges.append(
                    (-start_pixel_id - 1, -start_pixel_id - 1)
                )
            else:
                pixel_ranges.append(
                    (start_pixel_id, read_utf8_like_signed_int(self))
                )

        adc_samples = np.zeros(
            (num_gains, num_pixels, num_samples),
            dtype='u2'
        )
        n_pixels_signal = sum(p[1] - p[0] for p in pixel_ranges)
        data = self.read()
        adc_samples_signal, bytes_read = unsigned_varint_arrays_differential(
            data, n_arrays=num_gains * n_pixels_signal, n_elements=num_samples,
        )

        for i_gain in range(num_gains):
            for pixel_range in pixel_ranges:
                for i_array, i_pix in enumerate(range(*pixel_range)):
                    adc_samples[i_gain, i_pix, :] = adc_samples_signal[i_gain, i_array]
        return adc_samples

    def _parse_in_not_zero_suppressed_mode(
        self,
        num_gains,
        num_pixels,
        num_samples,
    ):

        data = self.read()
        adc_samples, bytes_read = unsigned_varint_arrays_differential(
            data, n_arrays=num_gains * num_pixels, n_elements=num_samples,
        )

        return adc_samples.reshape(
            num_gains, num_pixels, num_samples
        ).astype('u2')


class SimTelTelImage(EventIOObject):
    eventio_type = 2014

    def parse_data_field(self):
        assert_exact_version(self, supported_version=5)
        self.seek(0)

        flags = self.header.id
        tel_image = {}
        tel_image['flags'] = flags
        tel_image['flags_hex'] = hex(flags)
        tel_image['telescope_id'] = (
            (flags & 0xff) | (flags & 0x3f000000) >> 16
        )
        tel_image['cut_id'] = (flags & 0xff000) >> 12
        tel_image['pixels'] = read_short(self)
        tel_image['num_sat'] = read_short(self)

        # from version 6 on
        # pixels = read_utf8_like_signed_int(self)  # from version 6 on
        # num_sat = read_utf8_like_signed_int(self)

        if tel_image['num_sat'] > 0:
            tel_image['clip_amp'] = read_float(self)

        tel_image['amplitude'] = read_float(self)
        tel_image['x'] = read_float(self)
        tel_image['y'] = read_float(self)
        tel_image['phi'] = read_float(self)
        tel_image['l'] = read_float(self)
        tel_image['w'] = read_float(self)
        tel_image['num_conc'] = read_short(self)
        tel_image['concentration'] = read_float(self)

        if flags & 0x100:
            tel_image['x_err'] = read_float(self)
            tel_image['y_err'] = read_float(self)
            tel_image['phi_err'] = read_float(self)
            tel_image['l_err'] = read_float(self)
            tel_image['w_err'] = read_float(self)

        if flags & 0x200:
            tel_image['skewness'] = read_float(self)
            tel_image['skewness_err'] = read_float(self)
            tel_image['kurtosis'] = read_float(self)
            tel_image['kurtosis_err'] = read_float(self)

        if flags & 0x400:
            # from v6 on this is crazy int
            num_hot = read_short(self)
            tel_image['num_hot'] = num_hot
            tel_image['hot_amp'] = read_array(self, 'f4', num_hot)
            # from v6 on this is array of crazy int
            tel_image['hot_pixel'] = read_array(self, 'i2', num_hot)

        if flags & 0x800:
            tel_image['tm_slope'] = read_float(self)
            tel_image['tm_residual'] = read_float(self)
            tel_image['tm_width1'] = read_float(self)
            tel_image['tm_width2'] = read_float(self)
            tel_image['tm_rise'] = read_float(self)

        return tel_image


class SimTelShower(EventIOObject):
    eventio_type = 2015

    def parse_data_field(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)

        shower = {}
        result_bits = self.header.id
        shower['result_bits'] = result_bits
        shower['num_trg'] = read_short(self)
        shower['num_read'] = read_short(self)
        shower['num_img'] = read_short(self)
        shower['img_pattern'] = read_int(self)

        if result_bits & 0x01:
            shower['Az'] = read_float(self)
            shower['Alt'] = read_float(self)

        if result_bits & 0x02:
            shower['err_dir1'] = read_float(self)
            shower['err_dir2'] = read_float(self)
            shower['err_dir3'] = read_float(self)

        if result_bits & 0x04:
            shower['xc'] = read_float(self)
            shower['yc'] = read_float(self)

        if result_bits & 0x08:
            shower['err_core1'] = read_float(self)
            shower['err_core2'] = read_float(self)
            shower['err_core3'] = read_float(self)

        if result_bits & 0x10:
            shower['mscl'] = read_float(self)
            shower['mscw'] = read_float(self)

        if result_bits & 0x20:
            shower['err_mscl'] = read_float(self)
            shower['err_mscw'] = read_float(self)

        if result_bits & 0x40:
            shower['energy'] = read_float(self)

        if result_bits & 0x80:
            shower['err_energy'] = read_float(self)

        if result_bits & 0x0100:
            shower['xmax'] = read_float(self)

        if result_bits & 0x0200:
            shower['err_xmax'] = read_float(self)

        return shower


class SimTelPixelTiming(EventIOObject):
    eventio_type = 2016

    def parse_data_field(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)

        pixel_timing = {}
        pixel_timing['num_pixels'] = read_short(self)
        pixel_timing['num_gains'] = read_short(self)
        pixel_timing['before_peak'] = read_short(self)
        pixel_timing['after_peak'] = read_short(self)

        pixel_timing['with_sum'] = (
            (pixel_timing['before_peak'] >= 0)
            and (pixel_timing['after_peak'] >= 0)
        )

        list_type = read_short(self)
        assert list_type in (1, 2), "list_type has to be 1 or 2"
        list_size = read_short(self)
        pixel_timing['pixel_list'] = read_array(
            self, 'i2', list_size * list_type)
        pixel_timing['threshold'] = read_short(self)
        pixel_timing['glob_only_selected'] = pixel_timing['threshold'] < 0
        pixel_timing['num_types'] = read_short(self)

        pixel_timing['time_type'] = read_array(
            self, 'i2', pixel_timing['num_types'])
        pixel_timing['time_level'] = read_array(
            self, 'f4', pixel_timing['num_types'])

        pixel_timing['granularity'] = read_float(self)
        pixel_timing['peak_global'] = read_float(self)

        if list_type == 1:
            pixel_timing.update(self._parse_list_type_1(**pixel_timing))
        else:
            pixel_timing.update(self._parse_list_type_2(**pixel_timing))

    def _parse_list_type_1(
        self,
        pixel_list,
        num_types,
        num_gains,
        granularity,
        num_pixels,
        with_sum,
        glob_only_selected,
        **kwargs
    ):
        timval = np.zeros((num_pixels, num_types), dtype='f4')
        # The first timing element is always initialised to indicate unknown.
        timval[:, 0] = -1

        pulse_sum_loc = np.zeros((num_gains, num_pixels), dtype='i4')
        pulse_sum_glob = np.zeros((num_gains, num_pixels), dtype='i4')

        data = self.read()
        pos = 0

        for i_pix in pixel_list:
            timval[i_pix, :] = granularity * np.frombuffer(
                data, count=num_types, dtype='<i2', offset=pos,
            )
            pos += num_types * 2

            if with_sum:
                pulse_sum_loc[:, i_pix], length = varint_array(
                    data, n_elements=num_gains, offset=pos
                )
                pos += length

                if glob_only_selected:
                    pulse_sum_glob[:, i_pix], length = varint_array(
                        data, n_elements=num_gains, offset=pos
                    )
                    pos += length

        if with_sum and len(pixel_list) > 0 and not glob_only_selected:
            pulse_sum_glob = varint_array(
                data, n_elements=num_gains * num_pixels, offset=pos,
            ).reshape(num_gains, num_pixels)

        return {
            'timval': timval,
            'pulse_sum_glob': pulse_sum_glob,
            'pulse_sum_loc': pulse_sum_loc,
        }

    def _parse_list_type_2(
        self,
        pixel_list,
        num_types,
        num_gains,
        num_pixels,
        with_sum,
        glob_only_selected,
        granularity,
        **kwargs
    ):
        timval = np.zeros((num_pixels, num_types), dtype='f4')
        # The first timing element is always initialised to indicate unknown.
        timval[:, 0] = -1

        pulse_sum_loc = np.zeros((num_gains, num_pixels), dtype='i4')
        pulse_sum_glob = np.zeros((num_gains, num_pixels), dtype='i4')

        for start, stop in np.array(pixel_list).reshape(-1, 2):
            for i_pix in range(start, stop + 1):
                for i_type in range(num_types):
                    timval[i_pix, i_type] = granularity * read_short(self)

                if with_sum:
                    for i_gain in range(num_gains):
                        pulse_sum_loc[i_gain, i_pix] = read_utf8_like_signed_int(self)

                    if glob_only_selected:
                        for i_gain in range(num_gains):
                            pulse_sum_glob[i_gain, i_pix] = read_utf8_like_signed_int(self)

        if with_sum and len(pixel_list) > 0 and not glob_only_selected:
            for i_gain in range(num_gains):
                for i_pix in range(num_pixels):
                    pulse_sum_glob[i_gain, i_pix] = read_utf8_like_signed_int(self)

        return {
            'timval': timval,
            'pulse_sum_glob': pulse_sum_glob,
            'pulse_sum_loc': pulse_sum_loc,
        }


class SimTelPixelCalib(EventIOObject):
    eventio_type = 2017


class SimTelMCShower(EventIOObject):
    eventio_type = 2020

    def parse_data_field(self):
        assert_max_version(self, 2)

        self.seek(0)
        mc = {}
        mc['shower'] = self.header.id
        mc['primary_id'] = read_int(self)
        mc['energy'] = read_float(self)
        mc['azimuth'] = read_float(self)
        mc['altitude'] = read_float(self)
        if self.header.version >= 1:
            mc['depth_start'] = read_float(self)
        mc['h_first_int'] = read_float(self)
        mc['xmax'] = read_float(self)
        if self.header.version >= 1:
            mc['hmax'] = read_float(self)
            mc['emax'] = read_float(self)
            mc['cmax'] = read_float(self)
        else:
            mc['hmax'] = mc['emax'] = mc['cmax'] = 0.0

        mc['n_profiles'] = read_short(self)
        mc['profiles'] = []
        for i in range(mc['n_profiles']):
            p = {}
            p['id'] = read_int(self)
            p['num_steps'] = read_int(self)
            p['start'] = read_float(self)
            p['end'] = read_float(self)
            p['content'] = read_array(self, dtype='<f4', count=p['num_steps'])
            mc['profiles'].append(p)

        if self.header.version >= 2:
            h = read_next_header(self, toplevel=False)
            assert h.type == 1215
            mc['mc_extra_params'] = MC_Extra_Params(h, self).parse_data_field()
        return mc


class MC_Extra_Params(EventIOObject):
    eventio_type = 1215

    def parse_data_field(self):
        self.seek(0)
        ep = {
            'weight': read_float(self),
            'n_iparam': read_utf8_like_unsigned_int(self),
            'n_fparam': read_utf8_like_unsigned_int(self),
        }
        if ep['n_iparam'] > 0:
            ep['iparam'] = read_array(self, dtype='<i4', count=ep['n_iparam'])
        if ep['n_fparam'] > 0:
            ep['fparam'] = read_array(self, dtype='<f4', count=ep['n_iparam'])
        return ep


class SimTelMCEvent(EventIOObject):
    eventio_type = 2021

    def parse_data_field(self):
        ''' '''
        assert_exact_version(self, supported_version=1)
        self.seek(0)

        return {
            'event': self.header.id,
            'shower_num': read_int(self),
            'xcore': read_float(self),
            'ycore': read_float(self),
            # 'aweight': read_float(self),  # only in version 2
        }


class SimTelTelMoni(EventIOObject):
    eventio_type = 2022

    def parse_data_field(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)

        telescope_id = (
            (self.header.id & 0xff)
            | ((self.header.id & 0x3f000000) >> 16)
        )

        # what: denotes what has changed (since last report?)
        what = ((self.header.id & 0xffff00) >> 8) & 0xffff
        known = read_short(self)   # C-code used |= instead of = here.
        new_parts = read_short(self)
        monitor_id = read_int(self)
        moni_time = read_time(self)

        #  Dimensions of various things
        # version 0
        ns, np, nd, ng = read_from(self, '<hhhh')
        # in version 1 this uses crazy 32bit ints
        # ns = read_utf8_like_signed_int(self)
        # np = read_utf8_like_signed_int(self)
        # nd = read_utf8_like_signed_int(self)
        # ng = read_utf8_like_signed_int(self)

        result = {
            'telescope_id': telescope_id,
            'what': what,
            'known': known,
            'new_parts': new_parts,
            'monitor_id': monitor_id,
            'moni_time': moni_time,
        }
        part_parser_args = {
            'num_sectors': ns,
            'num_gains': ng,
            'num_pixels': np,
            'num_drawers': nd,
        }
        result.update(part_parser_args)

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
            'status_bits': read_int(self),
        }

    def _counts_and_rates_changed__what_and_0x02(
        self, num_sectors, **kwargs
    ):
        return {
            'trig_time': read_time(self),
            'coinc_count': read_int(self),
            'event_count': read_int(self),
            'trigger_rate': read_float(self),
            'sector_rate': read_array(self, 'f4', num_sectors),
            'event_rate': read_float(self),
            'data_rate': read_float(self),
            'mean_significant': read_float(self),
        }

    def _pedestal_and_noice_changed__what_and_0x04(
        self, num_gains, num_pixels, **kwargs
    ):
        return {
            'ped_noise_time': read_time(self),
            'num_ped_slices': read_short(self),
            'pedestal': read_array(
                self, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
            'noise': read_array(
                self, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
        }

    def _HV_and_temp_changed__what_and_0x08(
        self, num_pixels, num_drawers, **kwargs
    ):
        hv_temp_time = read_time(self)
        num_drawer_temp = read_short(self)
        num_camera_temp = read_short(self)
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

    def _pixel_scalers_DC_i_changed__what_and_0x10(
        self, num_pixels, **kwargs
    ):
        return {
            'dc_rate_time': read_time(self),
            'current': read_array(self, 'u2', num_pixels),
            'scaler': read_array(self, 'u2', num_pixels),
        }

    def _HV_thresholds_changed__what_and_0x20(
        self, num_pixels, num_drawers, **kwargs
    ):
        return {
            'hv_thr_time': read_time(self),
            'hv_dac': read_array(self, 'u2', num_pixels),
            'thresh_dac': read_array(self, 'u2', num_drawers),
            'hv_set': read_array(self, 'B', num_pixels),
            'trig_set': read_array(self, 'B', num_pixels),
        }

    def _DAQ_config_changed__what_and_0x40(
        self, **kwargs
    ):
        return {
            'set_daq_time': read_time(self),
            'daq_conf': read_short(self),
            'daq_scaler_win': read_short(self),
            'daq_nd': read_short(self),
            'daq_acc': read_short(self),
            'daq_nl': read_short(self),
        }


class SimTelLasCal(TelescopeObject):
    eventio_type = 2023

    def parse_data_field(self):
        ''' '''
        assert_exact_version(self, supported_version=2)
        self.seek(0)

        num_pixels = read_short(self)
        num_gains = read_short(self)
        lascal_id = read_int(self)
        calib = read_array(
            self, 'f4', num_gains * num_pixels
        ).reshape(num_gains, num_pixels)

        tmp_ = read_array(self, 'f4', num_gains * 2).reshape(num_gains, 2)
        max_int_frac = tmp_[:, 0]
        max_pixtm_frac = tmp_[:, 1]

        tm_calib = read_array(
            self, 'f4', num_gains * num_pixels
        ).reshape(num_gains, num_pixels)

        return {
            'telescope_id': self.telescope_id,
            'lascal_id': lascal_id,
            'calib': calib,
            'max_int_frac': max_int_frac,
            'max_pixtm_frac': max_pixtm_frac,
            'tm_calib': tm_calib,
        }


class SimTelRunStat(EventIOObject):
    eventio_type = 2024


class SimTelMCRunStat(EventIOObject):
    eventio_type = 2025


class SimTelMCPeSum(EventIOObject):
    eventio_type = 2026

    def parse_data_field(self):
        assert_exact_version(self, supported_version=2)
        self.seek(0)

        event = self.header.id
        shower_num = read_int(self)
        num_tel = read_int(self)
        num_pe = read_array(self, 'i4', num_tel)
        num_pixels = read_array(self, 'i4', num_tel)

        # NOTE:
        # I don't see how we can speed this up easily since the length
        # of this thing is not known upfront.

        # pix_pe: a list (running over telescope_id)
        #         of 2-tuples: (pixel_id, pe)
        pix_pe = []
        for n_pe, n_pixels in zip(num_pe, num_pixels):
            if n_pe <= 0 or n_pixels <= 0:
                continue
            non_empty = read_short(self)
            pixel_id = read_array(self, 'i2', non_empty)
            pe = read_array(self, 'i4', non_empty)
            pix_pe.append(pixel_id, pe)

        photons = read_array(self, 'f4', num_tel)
        photons_atm = read_array(self, 'f4', num_tel)
        photons_atm_3_6 = read_array(self, 'f4', num_tel)
        photons_atm_qe = read_array(self, 'f4', num_tel)
        photons_atm_400 = read_array(self, 'f4', num_tel)

        return {
            'event': event,
            'shower_num': shower_num,
            'num_tel': num_tel,
            'num_pe': num_pe,
            'num_pixels': num_pixels,
            'pix_pe': pix_pe,
            'photons': photons,
            'photons_atm': photons_atm,
            'photons_atm_3_6': photons_atm_3_6,
            'photons_atm_qe': photons_atm_qe,
            'photons_atm_400': photons_atm_400,
        }


class SimTelPixelList(EventIOObject):
    eventio_type = 2027

    def parse_data_field(self):
        # even in the prod3b version of Max N the objects
        # of type 2027 seem to be of version 0 only.
        # not sure if version 1 was ever produced.
        assert_exact_version(self, supported_version=0)

        self.seek(0)

        code = self.header.id // int(1e6)
        telescope = self.header.id % int(1e6)

        pixels = read_short(self)
        # in version 1 pixels is a crazy int

        pixel_list = read_array(self, 'i2', pixels)
        # in version 1 pixel_list is an array of crazy int

        return {
            'code': code,
            'telescope': telescope,
            'pixels': pixels,
            'pixel_list': pixel_list,
        }


class SimTelCalibEvent(EventIOObject):
    eventio_type = 2028


def merge_structured_arrays_into_dict(arrays):
    result = dict()
    for array in arrays:
        for name in array.dtype.names:
            result[name] = array[name]
    return result
