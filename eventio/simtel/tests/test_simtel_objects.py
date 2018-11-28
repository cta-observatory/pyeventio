from pkg_resources import resource_filename
from pytest import approx
import numpy as np


test_file = resource_filename('eventio', 'resources/gamma_test.simtel.gz')


def find_type(f, eventio_type):
    o = next(f)
    while not isinstance(o, eventio_type):
        o = next(f)

    if not isinstance(o, eventio_type):
        raise ValueError('Type {} not found'.format(eventio_type))

    return o


def test_run_heder():
    from eventio import EventIOFile
    from eventio.simtel import SimTelRunHeader

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelRunHeader)

        data = o.parse_data_field()
        data['observer'] = b'bernlohr@lfc371.mpi-hd.mpg.de'
        data['target'] = b'Monte Carlo beach'


def test_2002():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamSettings

    with EventIOFile(test_file) as f:
        obj = find_type(f, SimTelCamSettings)

        # first camera should be the LST
        camera_data = obj.parse_data_field()
        assert camera_data['telescope_id'] == 1
        assert camera_data['n_pixels'] == 1855
        assert camera_data['focal_length'] == 28.0
        assert len(camera_data['pixel_x']) == 1855
        assert len(camera_data['pixel_y']) == 1855


def test_telid():
    from eventio.simtel.objects import SimTelTelEvent

    assert SimTelTelEvent.type_to_telid(3305) == 205
    assert SimTelTelEvent.type_to_telid(3205) == 105
    assert SimTelTelEvent.type_to_telid(2203) == 3


def test_track():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelEvent, SimTelTrackEvent

    with EventIOFile(test_file) as f:

        # search for first event
        o = find_type(f, SimTelEvent)
        s = find_type(o, SimTelTrackEvent)

        pointing = s.parse_data_field()
        assert 'azimuth_raw' in pointing.dtype.names
        assert 'altitude_raw' in pointing.dtype.names


def test_2005():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelDisable

    with EventIOFile(test_file) as f:
        obj = next(f)
        while obj.header.type != SimTelPixelDisable.eventio_type:
            obj = next(f)

        # first camera should be the LST
        pixel_disable = obj.parse_data_field()

        assert pixel_disable['telescope_id'] == 1
        assert pixel_disable['num_trig_disabled'] == 0
        assert pixel_disable['num_HV_disabled'] == 0
        assert len(pixel_disable['trigger_disabled']) == 0
        assert len(pixel_disable['HV_disabled']) == 0


def test_2005_all_objects():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelDisable

    with EventIOFile(test_file) as f:
        all_2005_obs = [
            o for o in f
            if o.header.type == SimTelPixelDisable.eventio_type
        ]

        for i, o in enumerate(all_2005_obs):
            # first camera should be the LST
            pixel_disable = o.parse_data_field()

            assert pixel_disable['telescope_id'] == i + 1
            assert pixel_disable['num_trig_disabled'] == 0
            assert pixel_disable['num_HV_disabled'] == 0
            assert len(pixel_disable['trigger_disabled']) == 0
            assert len(pixel_disable['HV_disabled']) == 0


def test_pixelset():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelset

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelPixelset)

        assert o.telescope_id == 1
        pixelset = o.parse_data_field()

        assert pixelset['num_pixels'] == 1855


def test_2006_all():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamsoftset

    with EventIOFile(test_file) as f:
        all_2006_obs = [
            o for o in f
            if o.header.type == SimTelCamsoftset.eventio_type
        ]

        for i, o in enumerate(all_2006_obs):

            d = o.parse_data_field()

            # assert parse_data_field() consumed all data from o
            assert len(o.read()) == 0

            # now check the values
            assert d['telescope_id'] == i + 1
            assert d['dyn_trig_mode'] == 0
            assert d['dyn_trig_threshold'] == 0
            assert d['dyn_HV_mode'] == 0
            assert d['dyn_HV_threshold'] == 0
            assert d['data_red_mode'] == 0
            assert d['zero_sup_mode'] == 0
            assert d['zero_sup_num_thr'] == 0
            assert len(d['zero_sup_thresholds']) == 0
            assert d['unbiased_scale'] == 0
            assert d['dyn_ped_mode'] == 0
            assert d['dyn_ped_events'] == 0
            assert d['dyn_ped_period'] == 0
            assert d['monitor_cur_period'] == 0
            assert d['report_cur_period'] == 0
            assert d['monitor_HV_period'] == 0
            assert d['report_HV_period'] == 0


def test_2007_all():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPointingCor

    with EventIOFile(test_file) as f:
        all_2007_obs = [
            o for o in f
            if o.header.type == SimTelPointingCor.eventio_type
        ]

        for i, o in enumerate(all_2007_obs):

            d = o.parse_data_field()

            # assert parse_data_field() consumed all data from o
            assert len(o.read()) == 0

            # now check the values
            assert d['telescope_id'] == i + 1
            assert d['function_type'] == 0
            assert d['num_param'] == 0
            assert len(d['pointing_param']) == 0


def test_2008():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTrackSet

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelTrackSet)
        assert o.telescope_id == 1
        tracking_info = o.parse_data_field()

        assert tracking_info['range_low_az'] == 0.0
        assert tracking_info['range_low_alt'] == 0.0
        assert tracking_info['range_high_az'] == approx(2 * np.pi)
        assert tracking_info['range_high_alt'] == approx(2 * np.pi)


def test_2021_all():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelMCEvent

    with EventIOFile(test_file) as f:
        all_2021_obs = [
            o for o in f
            if o.header.type == SimTelMCEvent.eventio_type
        ]

        for i, o in enumerate(all_2021_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            assert len(o.read()) == 0

            assert d['shower_num'] == d['event'] // 100
            '''
            {
                'event': 11909,
                'shower_num': 119,
                'xcore': 1050.17626953125,
                'ycore': 1743.0797119140625
            }
            '''


def test_2023_all():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelLasCal

    with EventIOFile(test_file) as f:
        all_2023_obs = [
            o for o in f
            if o.header.type == SimTelLasCal.eventio_type
        ]

        for i, o in enumerate(all_2023_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            assert len(o.read()) == 0

            assert d['telescope_id'] ==  i + 1
            assert d['lascal_id'] == 2

    '''
    {
    'telescope_id': 1,
    'known': array([[ True,  True,  True, ...,  True,  True,  True]]),
    'lascal_id': 2,
    'max_int_frac': array([0.], dtype=float32),
    'max_pixtm_frac': array([0.], dtype=float32),
    'calib': array([[0.02838226, 0.02617863, 0.02520496, ..., 0.02812363, 0.02769747, 0.02691549]], dtype=float32),
    'tm_calib': array([[-21.383808, -21.283247, -21.452444, ..., -22.023653, -21.650948, -21.601557]], dtype=float32)}
    '''
