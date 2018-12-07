''' Implementations of the simtel_array EventIO object types '''
import numpy as np
from io import BytesIO
import struct
from ..base import EventIOObject, read_next_header_sublevel
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
from ..header import bool_bit_from_pos
from ..var_int import (
    unsigned_varint_arrays_differential,
    varint_array,
    varint,
)
from ..version_handling import (
    assert_exact_version,
    assert_max_version,
    assert_version_in
)


def read_remaining_with_check(byte_stream, length):
    pos = byte_stream.tell()
    data = byte_stream.read()
    if len(data) < (length - pos):
        raise EOFError('File seems to be truncated')
    return data


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

    def parse(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class HistoryConfig(EventIOObject):
    eventio_type = 72

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.timestamp = read_int(self)

    def parse(self):
        self.seek(4)  # skip the int, we already read in init
        return read_eventio_string(self)


class RunHeader(EventIOObject):
    eventio_type = 2000
    from .runheader_dtypes import (
        build_dtype_part1,
        build_dtype_part2
    )

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.run_id = self.header.id

    def parse(self):
        '''See write_hess_runheader l. 184 io_hess.c '''
        assert_max_version(self, 2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        dt1 = RunHeader.build_dtype_part1(self.header.version)
        part1 = read_array(byte_stream, dtype=dt1, count=1)[0]

        dt2 = RunHeader.build_dtype_part2(
            self.header.version,
            part1['n_telescopes']
        )
        part2 = read_array(byte_stream, dtype=dt2, count=1)[0]

        # rest is two null-terminated strings
        target = read_eventio_string(byte_stream)
        observer = read_eventio_string(byte_stream)

        result = dict(zip(part1.dtype.names, part1))
        result.update(dict(zip(part2.dtype.names, part2)))
        result['target'] = target
        result['observer'] = observer

        return result


class MCRunHeader(EventIOObject):
    eventio_type = 2001

    def parse(self):
        assert_exact_version(self, 4)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        return {
            'shower_prog_id': read_int(byte_stream),
            'shower_prog_vers': read_int(byte_stream),
            'shower_prog_start': read_int(byte_stream),
            'detector_prog_id': read_int(byte_stream),
            'detector_prog_vers': read_int(byte_stream),
            'detector_prog_start': read_int(byte_stream),
            'obsheight': read_float(byte_stream),
            'num_showers': read_int(byte_stream),
            'num_use': read_int(byte_stream),
            'core_pos_mode': read_int(byte_stream),
            'core_range': read_array(byte_stream, 'f4', 2),
            'alt_range': read_array(byte_stream, 'f4', 2),
            'az_range': read_array(byte_stream, 'f4', 2),
            'diffuse': read_int(byte_stream),
            'viewcone': read_array(byte_stream, 'f4', 2),
            'E_range': read_array(byte_stream, 'f4', 2),
            'spectral_index': read_float(byte_stream),
            'B_total': read_float(byte_stream),
            'B_inclination': read_float(byte_stream),
            'B_declination': read_float(byte_stream),
            'injection_height': read_float(byte_stream),
            'atmosphere': read_int(byte_stream),
            'corsika_iact_options': read_int(byte_stream),
            'corsika_low_E_model': read_int(byte_stream),
            'corsika_high_E_model': read_int(byte_stream),
            'corsika_bunchsize': read_float(byte_stream),
            'corsika_wlen_min': read_float(byte_stream),
            'corsika_wlen_max': read_float(byte_stream),
            'corsika_low_E_detail': read_int(byte_stream),
            'corsika_high_E_detail': read_int(byte_stream),
        }


class CameraSettings(TelescopeObject):
    eventio_type = 2002

    def parse(self):
        assert_version_in(self, [0, 1, 2, 3, 4, 5])
        self.seek(0)
        byte_stream = BytesIO(self.read())

        n_pixels = read_int(byte_stream)

        cam = {'n_pixels': n_pixels, 'telescope_id': self.telescope_id}
        cam['focal_length'] = read_float(byte_stream)
        if self.header.version > 4:
            cam['effective_focal_length'] = read_float(byte_stream)

        cam['pixel_x'] = read_array(byte_stream, count=n_pixels, dtype='float32')
        cam['pixel_y'] = read_array(byte_stream, count=n_pixels, dtype='float32')

        if self.header.version >= 4:
            cam['curved_surface'] = read_utf8_like_signed_int(byte_stream)
            cam['pixels_parallel'] = read_utf8_like_signed_int(byte_stream)

            if cam['curved_surface']:
                cam['pixel_z'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_z'] = np.zeros(n_pixels, dtype='<f4')

            if not cam['pixels_parallel']:
                cam['nxpix'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
                cam['nypix'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
            else:
                cam['nxpix'] = cam['nypix'] = np.zeros(n_pixels, dtype='f4')

            cam['common_pixel_shape'] = read_utf8_like_signed_int(byte_stream)
            if not cam['common_pixel_shape']:
                cam['pixel_shape'] = np.array([
                    read_utf8_like_signed_int(byte_stream) for _ in range(n_pixels)
                ])
                cam['pixel_area'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
                cam['pixel_size'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_shape'] = np.repeat(read_utf8_like_signed_int(byte_stream), n_pixels)
                cam['pixel_area'] = np.repeat(read_float(byte_stream), n_pixels)
                cam['pixel_size'] = np.repeat(read_float(byte_stream), n_pixels)
        else:
            cam['curve_surface'] = 0
            cam['pixels_parallel'] = 1
            cam['common_pixel_shape'] = 0
            cam['pixel_z'] = np.zeros(n_pixels, dtype='f4')
            cam['nxpix'] = cam['nypix'] = np.zeros(n_pixels, dtype='f4')
            cam['pixel_shape'] = np.full(n_pixels, -1, dtype='f4')
            cam['pixel_area'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
            if self.header.version >= 1:
                cam['pixel_size'] = read_array(byte_stream, dtype='<f4', count=n_pixels)
            else:
                cam['pixel_size'] = np.zeros(n_pixels, dtype='f4')

        if self.header.version >= 2:
            cam['n_mirrors'] = read_int(byte_stream)
            cam['mirror_area'] = read_float(byte_stream)
        else:
            cam['n_mirrors'] = 0.0
            cam['mirror_area'] = 0.0

        if self.header.version >= 3:
            cam['cam_rot'] = read_float(byte_stream)
        else:
            cam['cam_rot'] = 0.0

        return cam


class CameraOrganization(TelescopeObject):
    eventio_type = 2003

    from .camorgan import read_sector_information

    def parse(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        num_pixels = read_int(byte_stream)
        num_drawers = read_int(byte_stream)
        num_gains = read_int(byte_stream)
        num_sectors = read_int(byte_stream)

        drawer = read_array(byte_stream, 'i2', num_pixels)
        card = read_array(
            byte_stream, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)
        chip = read_array(
            byte_stream, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)
        channel = read_array(
            byte_stream, 'i2', num_pixels * num_gains
        ).reshape(num_pixels, num_gains)

        data = read_remaining_with_check(byte_stream, self.header.length)
        pos = 0
        sectors, bytes_read = CameraOrganization.read_sector_information(
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


class PixelSettings(TelescopeObject):
    eventio_type = 2004
    from .pixelset import dt1, build_dt2, build_dt3, build_dt4

    def parse(self):
        assert_max_version(self, 2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        p1 = read_array(byte_stream, dtype=PixelSettings.dt1, count=1)[0]

        dt2 = PixelSettings.build_dt2(num_pixels=p1['num_pixels'])
        p2 = read_array(byte_stream, dtype=dt2, count=1)[0]

        dt3 = PixelSettings.build_dt3(
            self.header.version, num_drawers=p2['num_drawers']
        )
        p3 = read_array(byte_stream, dtype=dt3, count=1)[0]

        parts = [p1, p2, p3]
        if self.header.version >= 2:
            nrefshape = read_utf8_like_signed_int(byte_stream)
            lrefshape = read_utf8_like_signed_int(byte_stream)

            dt4 = PixelSettings.build_dt4(nrefshape, lrefshape)
            parts.append(read_array(byte_stream, dtype=dt4, count=1)[0])

        D = merge_structured_arrays_into_dict(parts)
        D['telescope_id'] = self.header.id
        return D


class DisabledPixels(EventIOObject):
    eventio_type = 2005

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def parse(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        num_trig_disabled = read_int(byte_stream)
        trigger_disabled = read_array(
            byte_stream,
            count=num_trig_disabled,
            dtype='i4'
        )
        num_HV_disabled = read_int(byte_stream)
        HV_disabled = read_array(byte_stream, count=num_trig_disabled, dtype='i4')

        return {
            'telescope_id': self.telescope_id,
            'num_trig_disabled': num_trig_disabled,
            'trigger_disabled': trigger_disabled,
            'num_HV_disabled': num_HV_disabled,
            'HV_disabled': HV_disabled,
        }


class CameraSoftwareSettings(EventIOObject):
    eventio_type = 2006

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = header.id

    def parse(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        dyn_trig_mode = read_int(byte_stream)
        dyn_trig_threshold = read_int(byte_stream)
        dyn_HV_mode = read_int(byte_stream)
        dyn_HV_threshold = read_int(byte_stream)
        data_red_mode = read_int(byte_stream)
        zero_sup_mode = read_int(byte_stream)
        zero_sup_num_thr = read_int(byte_stream)
        zero_sup_thresholds = read_array(byte_stream, 'i4', zero_sup_num_thr)
        unbiased_scale = read_int(byte_stream)
        dyn_ped_mode = read_int(byte_stream)
        dyn_ped_events = read_int(byte_stream)
        dyn_ped_period = read_int(byte_stream)
        monitor_cur_period = read_int(byte_stream)
        report_cur_period = read_int(byte_stream)
        monitor_HV_period = read_int(byte_stream)
        report_HV_period = read_int(byte_stream)

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


class PointingCorrection(TelescopeObject):
    eventio_type = 2007

    def parse(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        function_type = read_int(byte_stream)
        num_param = read_int(byte_stream)
        pointing_param = read_array(byte_stream, 'f4', num_param)

        return {
            'telescope_id': self.telescope_id,
            'function_type': function_type,
            'num_param': num_param,
            'pointing_param': pointing_param,
        }


class DriveSettings(TelescopeObject):
    eventio_type = 2008

    def parse(self):
        assert_exact_version(self, 0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        tracking_info = {}
        tracking_info['drive_type_az'] = read_short(byte_stream)
        tracking_info['drive_type_alt'] = read_short(byte_stream)
        tracking_info['zeropoint_az'] = read_float(byte_stream)
        tracking_info['zeropoint_alt'] = read_float(byte_stream)

        tracking_info['sign_az'] = read_float(byte_stream)
        tracking_info['sign_alt'] = read_float(byte_stream)
        tracking_info['resolution_az'] = read_float(byte_stream)
        tracking_info['resolution_alt'] = read_float(byte_stream)
        tracking_info['range_low_az'] = read_float(byte_stream)
        tracking_info['range_low_alt'] = read_float(byte_stream)
        tracking_info['range_high_az'] = read_float(byte_stream)
        tracking_info['range_high_alt'] = read_float(byte_stream)
        tracking_info['park_pos_az'] = read_float(byte_stream)
        tracking_info['park_pos_alt'] = read_float(byte_stream)

        return tracking_info


class TriggerInformation(EventIOObject):
    eventio_type = 2009

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.global_count = self.header.id

    def __repr__(self):
        return '{}[{}](shower_event_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        assert_max_version(self, 2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        event_info = {}
        event_info['cpu_time'] = read_time(byte_stream)
        event_info['gps_time'] = read_time(byte_stream)
        event_info['trigger_pattern'] = read_int(byte_stream)
        event_info['data_pattern'] = read_int(byte_stream)

        if self.header.version >= 1:
            tels_trigger = read_short(byte_stream)
            event_info['n_triggered_telescopes'] = tels_trigger

            event_info['triggered_telescopes'] = read_array(
                byte_stream, count=tels_trigger, dtype='<i2',
            )
            event_info['trigger_times'] = read_array(
                byte_stream, count=tels_trigger, dtype='<f4',
            )
            tels_data = read_short(byte_stream)
            event_info['n_telescopes_with_data'] = tels_data
            event_info['telescopes_with_data'] = read_array(
                byte_stream, count=tels_data, dtype='<i2'
            )

        if self.header.version >= 2:
            # konrad saves the trigger mask as crazy int, but it uses only 4 bits
            # so it should be indentical to a normal unsigned int with 1 byte
            event_info['teltrg_type_mask'] = read_array(
                byte_stream, count=tels_trigger, dtype='uint8'
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
                            t = read_float(byte_stream)
                            event_info['teltrg_time_by_type'][tel_id][trigger] = t

        return event_info


class TrackingPosition(EventIOObject):
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

    def parse(self):
        assert_exact_version(self, 0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        dt = []
        if self.has_raw:
            dt.extend([('azimuth_raw', '<f4'), ('altitude_raw', '<f4')])
        if self.has_cor:
            dt.extend([('azimuth_cor', '<f4'), ('altitude_cor', '<f4')])
        A = read_array(byte_stream, count=1, dtype=dt)[0]
        D = merge_structured_arrays_into_dict([A])
        D['telescope_id'] = self.telescope_id
        return D

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
        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.eventio_type,
            self.telescope_id,
        )


class TelescopeEvent(EventIOObject):
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


class ArrayEvent(EventIOObject):
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


class TelescopeEventHeader(TelescopeObject):
    eventio_type = 2011

    def __repr__(self):
        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        assert_max_version(self, 2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        event_head = {}
        event_head['loc_count'] = read_int(byte_stream)
        event_head['glob_count'] = read_int(byte_stream)
        event_head['cpu_time'] = read_time(byte_stream)
        event_head['gps_time'] = read_time(byte_stream)
        t = read_short(byte_stream)
        event_head['trg_source'] = t & 0xff

        pos = 0
        data = read_remaining_with_check(byte_stream, self.header.length)
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
                event_head['phys_addr'] = np.frombuffer(
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

        event_head['telescope_id'] = self.header.id
        return event_head


class ADCSums(EventIOObject):
    eventio_type = 2012

    def __init__(self, header, parent):
        super().__init__(header, parent)
        if self.header.version <= 1:
            self.telescope_id = (header.id >> 25) & 0x1f
        else:
            self.telescope_id = (header.id >> 12) & 0xffff

    def __repr__(self):
        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.telescope_id,
        )

    def parse(self):
        assert_exact_version(self, 3)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        flags = self.header.id
        raw = {'telescope_id': self.telescope_id}
        raw['zero_sup_mode'] = flags & 0x1f
        raw['data_red_mode'] = (flags >> 5) & 0x1f
        raw['list_known'] = (flags >> 10) & 0x01
        n_pixels = read_int(byte_stream)
        n_gains = read_short(byte_stream)

        if raw['data_red_mode'] != 0 or raw['zero_sup_mode'] != 0:
            raise NotImplementedError(
                'Currently no support for data_red_mode {} or zero_sup_mode{}'.format(
                    raw['data_red_mode'], raw['zero_sup_mode'],
                )
            )

        raw['adc_sums'] = []
        data = read_remaining_with_check(byte_stream, self.header.length)
        raw['adc_sums'], bytes_read = unsigned_varint_arrays_differential(
            data, n_arrays=n_gains, n_elements=n_pixels
        )

        try:
            return np.squeeze(raw['adc_sums'], axis=-1)
        except ValueError:
            return raw['adc_sums']


class ADCSamples(EventIOObject):
    eventio_type = 2013

    def __init__(self, header, parent):
        super().__init__(header, parent)
        flags_ = header.id
        self._zero_sup_mode = flags_ & 0x1f
        self._data_red_mode = (flags_ >> 5) & 0x1f
        self._list_known = bool((flags_ >> 10) & 0x01)

        #  !! WTF: raw->zero_sup_mode |= zero_sup_mode << 5

        self.telescope_id = (flags_ >> 12) & 0xffff

    def parse(self):
        assert_exact_version(self, supported_version=3)
        unsupported = (
            self._zero_sup_mode != 0
            or self._data_red_mode != 0
            or self._list_known
        )
        if unsupported:
            raise NotImplementedError

        self.seek(0)
        byte_stream = BytesIO(self.read())

        args = {
            'byte_stream': byte_stream,
            'num_pixels': read_int(byte_stream),
            'num_gains': read_short(byte_stream),
            'num_samples': read_short(byte_stream),
        }
        if self._zero_sup_mode:
            result = self._parse_in_zero_suppressed_mode(**args)
        else:
            result = self._parse_in_not_zero_suppressed_mode(**args)

        try:
            result = np.squeeze(result, axis=-1)
        except ValueError:
            pass

        return result

    def _parse_in_zero_suppressed_mode(
        self,
        byte_stream,
        num_gains,
        num_pixels,
        num_samples,
    ):
        list_size = read_utf8_like_signed_int(byte_stream)
        pixel_ranges = []
        for _ in range(list_size):
            start_pixel_id = read_utf8_like_signed_int(byte_stream)
            if start_pixel_id < 0:
                pixel_ranges.append(
                    (-start_pixel_id - 1, -start_pixel_id - 1)
                )
            else:
                pixel_ranges.append(
                    (start_pixel_id, read_utf8_like_signed_int(byte_stream))
                )

        adc_samples = np.zeros(
            (num_gains, num_pixels, num_samples),
            dtype='u2'
        )
        n_pixels_signal = sum(p[1] - p[0] for p in pixel_ranges)
        data = read_remaining_with_check(byte_stream, self.header.length)
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
        byte_stream,
        num_gains,
        num_pixels,
        num_samples,
    ):

        data = read_remaining_with_check(byte_stream, self.header.length)
        adc_samples, bytes_read = unsigned_varint_arrays_differential(
            data, n_arrays=num_gains * num_pixels, n_elements=num_samples,
        )

        return adc_samples.reshape(
            num_gains, num_pixels, num_samples
        ).astype('u2')


class ImageParameters(EventIOObject):
    eventio_type = 2014

    def __repr__(self):
        telescope_id = (
            (self.header.id & 0xff) | (self.header.id & 0x3f000000) >> 16
        )

        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            telescope_id,
        )

    def parse(self):
        assert_exact_version(self, supported_version=5)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        flags = self.header.id
        tel_image = {}
        tel_image['flags'] = flags
        tel_image['flags_hex'] = hex(flags)
        tel_image['telescope_id'] = (
            (flags & 0xff) | (flags & 0x3f000000) >> 16
        )
        tel_image['cut_id'] = (flags & 0xff000) >> 12
        tel_image['pixels'] = read_short(byte_stream)
        tel_image['num_sat'] = read_short(byte_stream)

        # from version 6 on
        # pixels = read_utf8_like_signed_int(self)  # from version 6 on
        # num_sat = read_utf8_like_signed_int(self)

        if tel_image['num_sat'] > 0:
            tel_image['clip_amp'] = read_float(byte_stream)

        tel_image['amplitude'] = read_float(byte_stream)
        tel_image['x'] = read_float(byte_stream)
        tel_image['y'] = read_float(byte_stream)
        tel_image['phi'] = read_float(byte_stream)
        tel_image['l'] = read_float(byte_stream)
        tel_image['w'] = read_float(byte_stream)
        tel_image['num_conc'] = read_short(byte_stream)
        tel_image['concentration'] = read_float(byte_stream)

        if flags & 0x100:
            tel_image['x_err'] = read_float(byte_stream)
            tel_image['y_err'] = read_float(byte_stream)
            tel_image['phi_err'] = read_float(byte_stream)
            tel_image['l_err'] = read_float(byte_stream)
            tel_image['w_err'] = read_float(byte_stream)

        if flags & 0x200:
            tel_image['skewness'] = read_float(byte_stream)
            tel_image['skewness_err'] = read_float(byte_stream)
            tel_image['kurtosis'] = read_float(byte_stream)
            tel_image['kurtosis_err'] = read_float(byte_stream)

        if flags & 0x400:
            # from v6 on this is crazy int
            num_hot = read_short(byte_stream)
            tel_image['num_hot'] = num_hot
            tel_image['hot_amp'] = read_array(byte_stream, 'f4', num_hot)
            # from v6 on this is array of crazy int
            tel_image['hot_pixel'] = read_array(byte_stream, 'i2', num_hot)

        if flags & 0x800:
            tel_image['tm_slope'] = read_float(byte_stream)
            tel_image['tm_residual'] = read_float(byte_stream)
            tel_image['tm_width1'] = read_float(byte_stream)
            tel_image['tm_width2'] = read_float(byte_stream)
            tel_image['tm_rise'] = read_float(byte_stream)

        return tel_image


class StereoReconstruction(EventIOObject):
    eventio_type = 2015

    def __repr__(self):
        return '{}[{}](result_bits={})'.format(
            self.__class__.__name__,
            self.header.type,
            np.binary_repr(self.header.id, width=12),
        )

    def parse(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        shower = {}
        result_bits = self.header.id
        shower['result_bits'] = result_bits
        shower['num_trg'] = read_short(byte_stream)
        shower['num_read'] = read_short(byte_stream)
        shower['num_img'] = read_short(byte_stream)
        shower['img_pattern'] = read_int(byte_stream)

        if result_bits & 0x01:
            shower['Az'] = read_float(byte_stream)
            shower['Alt'] = read_float(byte_stream)

        if result_bits & 0x02:
            shower['err_dir1'] = read_float(byte_stream)
            shower['err_dir2'] = read_float(byte_stream)
            shower['err_dir3'] = read_float(byte_stream)

        if result_bits & 0x04:
            shower['xc'] = read_float(byte_stream)
            shower['yc'] = read_float(byte_stream)

        if result_bits & 0x08:
            shower['err_core1'] = read_float(byte_stream)
            shower['err_core2'] = read_float(byte_stream)
            shower['err_core3'] = read_float(byte_stream)

        if result_bits & 0x10:
            shower['mscl'] = read_float(byte_stream)
            shower['mscw'] = read_float(byte_stream)

        if result_bits & 0x20:
            shower['err_mscl'] = read_float(byte_stream)
            shower['err_mscw'] = read_float(byte_stream)

        if result_bits & 0x40:
            shower['energy'] = read_float(byte_stream)

        if result_bits & 0x80:
            shower['err_energy'] = read_float(byte_stream)

        if result_bits & 0x0100:
            shower['xmax'] = read_float(byte_stream)

        if result_bits & 0x0200:
            shower['err_xmax'] = read_float(byte_stream)

        return shower


class PixelTiming(EventIOObject):
    eventio_type = 2016
    from ..var_int import simtel_pixel_timing_parse_list_type_1 as _parse_list_type_1
    from ..var_int import simtel_pixel_timing_parse_list_type_2 as _parse_list_type_2

    def __repr__(self):
        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        assert_exact_version(self, supported_version=1)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        pixel_timing = {}
        pixel_timing['num_pixels'] = read_short(byte_stream)
        pixel_timing['num_gains'] = read_short(byte_stream)
        pixel_timing['before_peak'] = read_short(byte_stream)
        pixel_timing['after_peak'] = read_short(byte_stream)

        pixel_timing['with_sum'] = (
            (pixel_timing['before_peak'] >= 0)
            and (pixel_timing['after_peak'] >= 0)
        )

        list_type = read_short(byte_stream)
        assert list_type in (1, 2), "list_type has to be 1 or 2"
        list_size = read_short(byte_stream)
        pixel_timing['pixel_list'] = read_array(
            byte_stream, dtype='i2', count=list_size * list_type
        )
        pixel_timing['threshold'] = read_short(byte_stream)
        pixel_timing['glob_only_selected'] = pixel_timing['threshold'] < 0
        pixel_timing['num_types'] = read_short(byte_stream)

        pixel_timing['time_type'] = read_array(
            byte_stream, 'i2', count=pixel_timing['num_types']
        )
        pixel_timing['time_level'] = read_array(
            byte_stream, 'f4', count=pixel_timing['num_types']
        )

        pixel_timing['granularity'] = read_float(byte_stream)
        pixel_timing['peak_global'] = read_float(byte_stream)

        data = read_remaining_with_check(byte_stream, self.header.length)
        if list_type == 1:
            result, bytes_read = PixelTiming._parse_list_type_1(
                data,
                pixel_list=pixel_timing['pixel_list'],
                num_gains=pixel_timing['num_gains'],
                num_pixels=pixel_timing['num_pixels'],
                num_types=pixel_timing['num_types'],
                with_sum=pixel_timing['with_sum'],
                glob_only_selected=pixel_timing['glob_only_selected'],
                granularity=pixel_timing['granularity'],
            )
        else:
            result, bytes_read = PixelTiming._parse_list_type_2(
                data,
                pixel_list=pixel_timing['pixel_list'].reshape(-1, 2),
                num_gains=pixel_timing['num_gains'],
                num_pixels=pixel_timing['num_pixels'],
                num_types=pixel_timing['num_types'],
                with_sum=pixel_timing['with_sum'],
                glob_only_selected=pixel_timing['glob_only_selected'],
                granularity=pixel_timing['granularity'],
            )
        pixel_timing.update(result)
        return pixel_timing


class PixelCalibration(EventIOObject):
    eventio_type = 2017


class MCShower(EventIOObject):
    eventio_type = 2020

    def __init__(self, header, parent):
        super().__init__(header, parent)

    def __repr__(self):
        return '{}[{}](shower_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        assert_max_version(self, 2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        mc = {}
        mc['shower'] = self.header.id
        mc['primary_id'] = read_int(byte_stream)
        mc['energy'] = read_float(byte_stream)
        mc['azimuth'] = read_float(byte_stream)
        mc['altitude'] = read_float(byte_stream)
        if self.header.version >= 1:
            mc['depth_start'] = read_float(byte_stream)
        mc['h_first_int'] = read_float(byte_stream)
        mc['xmax'] = read_float(byte_stream)
        if self.header.version >= 1:
            mc['hmax'] = read_float(byte_stream)
            mc['emax'] = read_float(byte_stream)
            mc['cmax'] = read_float(byte_stream)
        else:
            mc['hmax'] = mc['emax'] = mc['cmax'] = 0.0

        mc['n_profiles'] = read_short(byte_stream)
        mc['profiles'] = []
        for i in range(mc['n_profiles']):
            p = {}
            p['id'] = read_int(byte_stream)
            p['num_steps'] = read_int(byte_stream)
            p['start'] = read_float(byte_stream)
            p['end'] = read_float(byte_stream)
            p['content'] = read_array(byte_stream, dtype='<f4', count=p['num_steps'])
            mc['profiles'].append(p)

        if self.header.version >= 2:
            h = read_next_header_sublevel(self)
            assert h.type == 1215
            mc['mc_extra_params'] = MCExtraParams(h, self).parse()
        return mc


class MCExtraParams(EventIOObject):
    eventio_type = 1215

    def parse(self):
        self.seek(0)
        byte_stream = BytesIO(self.read())

        ep = {
            'weight': read_float(byte_stream),
            'n_iparam': read_utf8_like_unsigned_int(byte_stream),
            'n_fparam': read_utf8_like_unsigned_int(byte_stream),
        }
        if ep['n_iparam'] > 0:
            ep['iparam'] = read_array(byte_stream, dtype='<i4', count=ep['n_iparam'])
        if ep['n_fparam'] > 0:
            ep['fparam'] = read_array(byte_stream, dtype='<f4', count=ep['n_iparam'])
        return ep


class MCEvent(EventIOObject):
    eventio_type = 2021
    dtypes = {
        1: np.dtype([('shower_num', 'i4'), ('xcore', 'f4'), ('ycore', 'f4')]),
        2: np.dtype([
            ('shower_num', 'i4'),
            ('xcore', 'f4'),
            ('ycore', 'f4'),
            ('aweight', 'f4')
        ]),
    }

    def __repr__(self):
        return '{}[{}](shower_event_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        ''' '''
        assert_version_in(self, (1, 2))
        self.seek(0)

        return read_array(
            self, dtype=self.dtypes[self.header.version], count=1
        )


class CameraMonitoring(EventIOObject):
    eventio_type = 2022

    def __init__(self, header, parent):
        super().__init__(header, parent)

        self.telescope_id = (
            (self.header.id & 0xff)
            | ((self.header.id & 0x3f000000) >> 16)
        )

    def __repr__(self):
        return '{}[{}](telescope_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.telescope_id,
        )

    def parse(self):
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        # what: denotes what has changed (since last report?)
        what = ((self.header.id & 0xffff00) >> 8) & 0xffff
        known = read_short(byte_stream)   # C-code used |= instead of = here.
        new_parts = read_short(byte_stream)
        monitor_id = read_int(byte_stream)
        moni_time = read_time(byte_stream)

        #  Dimensions of various things
        # version 0
        ns, np, nd, ng = read_from(byte_stream, '<hhhh')
        # in version 1 this uses crazy 32bit ints
        # ns = read_utf8_like_signed_int(byte_stream)
        # np = read_utf8_like_signed_int(byte_stream)
        # nd = read_utf8_like_signed_int(byte_stream)
        # ng = read_utf8_like_signed_int(byte_stream)

        result = {
            'telescope_id': self.telescope_id,
            'what': what,
            'known': known,
            'new_parts': new_parts,
            'monitor_id': monitor_id,
            'moni_time': moni_time,
        }
        part_parser_args = {
            'byte_stream': byte_stream,
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

        result['telescope_id'] = self.telescope_id
        return result

    def _nothing_changed_here(self, **kwargs):
        ''' dummy parser, invoked when this bit is not set '''
        return {}

    def _status_only_changed__what_and_0x01(self, byte_stream, **kwargs):
        return {
            'status_time': read_time(byte_stream),
            'status_bits': read_int(byte_stream),
        }

    def _counts_and_rates_changed__what_and_0x02(
        self, byte_stream, num_sectors, **kwargs
    ):
        return {
            'trig_time': read_time(byte_stream),
            'coinc_count': read_int(byte_stream),
            'event_count': read_int(byte_stream),
            'trigger_rate': read_float(byte_stream),
            'sector_rate': read_array(byte_stream, 'f4', num_sectors),
            'event_rate': read_float(byte_stream),
            'data_rate': read_float(byte_stream),
            'mean_significant': read_float(byte_stream),
        }

    def _pedestal_and_noice_changed__what_and_0x04(
        self, byte_stream, num_gains, num_pixels, **kwargs
    ):
        return {
            'ped_noise_time': read_time(byte_stream),
            'num_ped_slices': read_short(byte_stream),
            'pedestal': read_array(
                byte_stream, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
            'noise': read_array(
                byte_stream, 'f4', num_gains * num_pixels
            ).reshape((num_gains, num_pixels)),
        }

    def _HV_and_temp_changed__what_and_0x08(
        self, byte_stream, num_pixels, num_drawers, **kwargs
    ):
        hv_temp_time = read_time(byte_stream)
        num_drawer_temp = read_short(byte_stream)
        num_camera_temp = read_short(byte_stream)
        return {
            'hv_temp_time': hv_temp_time,
            'num_drawer_temp': num_drawer_temp,
            'num_camera_temp': num_camera_temp,
            'hv_v_mon': read_array(byte_stream, 'i2', num_pixels),
            'hv_i_mon': read_array(byte_stream, 'i2', num_pixels),
            'hv_stat': read_array(byte_stream, 'B', num_pixels),
            'drawer_temp': read_array(
                byte_stream, 'i2', num_drawers * num_drawer_temp
            ).reshape((num_drawers, num_drawer_temp)),
            'camera_temp': read_array(byte_stream, 'i2', num_camera_temp),
        }

    def _pixel_scalers_DC_i_changed__what_and_0x10(
        self, byte_stream, num_pixels, **kwargs
    ):
        return {
            'dc_rate_time': read_time(byte_stream),
            'current': read_array(byte_stream, 'u2', num_pixels),
            'scaler': read_array(byte_stream, 'u2', num_pixels),
        }

    def _HV_thresholds_changed__what_and_0x20(
        self, byte_stream, num_pixels, num_drawers, **kwargs
    ):
        return {
            'hv_thr_time': read_time(byte_stream),
            'hv_dac': read_array(byte_stream, 'u2', num_pixels),
            'thresh_dac': read_array(byte_stream, 'u2', num_drawers),
            'hv_set': read_array(byte_stream, 'B', num_pixels),
            'trig_set': read_array(byte_stream, 'B', num_pixels),
        }

    def _DAQ_config_changed__what_and_0x40(
        self, byte_stream, **kwargs
    ):
        return {
            'set_daq_time': read_time(byte_stream),
            'daq_conf': read_short(byte_stream),
            'daq_scaler_win': read_short(byte_stream),
            'daq_nd': read_short(byte_stream),
            'daq_acc': read_short(byte_stream),
            'daq_nl': read_short(byte_stream),
        }


class LaserCalibration(TelescopeObject):
    eventio_type = 2023

    def parse(self):
        assert_exact_version(self, supported_version=2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        num_pixels = read_short(byte_stream)
        num_gains = read_short(byte_stream)
        lascal_id = read_int(byte_stream)
        calib = read_array(
            byte_stream, 'f4', num_gains * num_pixels
        ).reshape(num_gains, num_pixels)

        tmp_ = read_array(byte_stream, 'f4', num_gains * 2).reshape(num_gains, 2)
        max_int_frac = tmp_[:, 0]
        max_pixtm_frac = tmp_[:, 1]

        tm_calib = read_array(
            byte_stream, 'f4', num_gains * num_pixels
        ).reshape(num_gains, num_pixels)

        return {
            'telescope_id': self.telescope_id,
            'lascal_id': lascal_id,
            'calib': calib,
            'max_int_frac': max_int_frac,
            'max_pixtm_frac': max_pixtm_frac,
            'tm_calib': tm_calib,
        }


class RunStatistics(EventIOObject):
    eventio_type = 2024


class MCRunStatistics(EventIOObject):
    eventio_type = 2025


class MCPhotoelectronSum(EventIOObject):
    eventio_type = 2026

    def __repr__(self):
        return '{}[{}](shower_event_id={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.id,
        )

    def parse(self):
        assert_exact_version(self, supported_version=2)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        event = self.header.id
        shower_num = read_int(byte_stream)
        num_tel = read_int(byte_stream)
        num_pe = read_array(byte_stream, 'i4', num_tel)
        num_pixels = read_array(byte_stream, 'i4', num_tel)

        # NOTE:
        # I don't see how we can speed this up easily since the length
        # of this thing is not known upfront.

        # pix_pe: a list (running over telescope_id)
        #         of 2-tuples: (pixel_id, pe)
        pix_pe = []
        for n_pe, n_pixels in zip(num_pe, num_pixels):
            if n_pe <= 0 or n_pixels <= 0:
                continue
            non_empty = read_short(byte_stream)
            pixel_id = read_array(byte_stream, 'i2', non_empty)
            pe = read_array(byte_stream, 'i4', non_empty)
            pix_pe.append(pixel_id, pe)

        photons = read_array(byte_stream, 'f4', num_tel)
        photons_atm = read_array(byte_stream, 'f4', num_tel)
        photons_atm_3_6 = read_array(byte_stream, 'f4', num_tel)
        photons_atm_qe = read_array(byte_stream, 'f4', num_tel)
        photons_atm_400 = read_array(byte_stream, 'f4', num_tel)

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


class PixelList(EventIOObject):
    eventio_type = 2027

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.telescope_id = self.header.id // 1000000
        self.code = self.telescope_id % 1000000

    def __repr__(self):
        return '{}[{}](telescope_id={}, code={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.telescopes_id,
            self.code,
        )

    def parse(self):
        # even in the prod3b version of Max N the objects
        # of type 2027 seem to be of version 0 only.
        # not sure if version 1 was ever produced.
        assert_exact_version(self, supported_version=0)
        self.seek(0)
        byte_stream = BytesIO(self.read())

        pixels = read_short(byte_stream)
        # in version 1 pixels is a crazy int

        pixel_list = read_array(byte_stream, 'i2', pixels)
        # in version 1 pixel_list is an array of crazy int

        return {
            'code': self.code,
            'telescope_id': self.telescope_id,
            'pixels': pixels,
            'pixel_list': pixel_list,
        }


class CalibrationEvent(EventIOObject):
    eventio_type = 2028


def merge_structured_arrays_into_dict(arrays):
    result = dict()
    for array in arrays:
        for name in array.dtype.names:
            result[name] = array[name]
    return result
