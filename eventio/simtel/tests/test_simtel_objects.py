from pkg_resources import resource_filename
import pytest
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


def test_70():
    from eventio import EventIOFile
    from eventio.simtel.objects import History

    with EventIOFile(test_file) as f:
        all_histories = [
            o for o in f
            if o.header.type == History.eventio_type
        ]
        for o in all_histories:
            assert isinstance(o, History)

            # make sure a History can be iterated and is never empty
            body_reached = False
            for x in o:
                body_reached = True
            assert body_reached


def test_71():
    from eventio import EventIOFile
    from eventio.simtel.objects import History, HistoryCommandLine

    with EventIOFile(test_file) as f:
        all_history_cmd_lines = []
        for o in f:
            if isinstance(o, History):
                for sub in o:
                    if isinstance(sub, HistoryCommandLine):
                        all_history_cmd_lines.append(sub)

        for o in all_history_cmd_lines:
            s = o.parse_data_field()
            assert s
            assert isinstance(s, bytes)


def test_72():
    from eventio import EventIOFile
    from eventio.simtel.objects import History, HistoryConfig

    with EventIOFile(test_file) as f:
        all_history_configs = []
        for o in f:
            if isinstance(o, History):
                for sub in o:
                    if isinstance(sub, HistoryConfig):
                        all_history_configs.append(sub)

        for o in all_history_configs:
            s = o.parse_data_field()
            assert s
            assert isinstance(s, bytes)


def test_2000():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelRunHeader

    with EventIOFile(test_file) as f:
        classes_under_test = [
            o for o in f
            if isinstance(o, SimTelRunHeader)
        ]
        # make sure we found some
        assert classes_under_test

        for o in classes_under_test:
            d = o.parse_data_field()
            assert d

            bytes_not_consumed = o.read()
            # DN: I do not know why two bytes, did not x-check
            assert len(bytes_not_consumed) == 2
            for byte_ in bytes_not_consumed:
                assert byte_ == 0


def test_2000_as_well():
    from eventio import EventIOFile
    from eventio.simtel import SimTelRunHeader

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelRunHeader)

        data = o.parse_data_field()
        data['observer'] = b'bernlohr@lfc371.mpi-hd.mpg.de'
        data['target'] = b'Monte Carlo beach'


@pytest.mark.xfail
def test_2001():
    assert False


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

@pytest.mark.xfail
def test_2003():
    assert False


def test_2004():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelset

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelPixelset)

        assert o.telescope_id == 1
        pixelset = o.parse_data_field()

        assert pixelset['num_pixels'] == 1855


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


def test_2006():
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


def test_2007():
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


def test_2009():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelEvent, SimTelCentEvent

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelEvent)
        s = find_type(o, SimTelCentEvent)

        data = s.parse_data_field()
        assert 'cpu_time' in data
        assert 'gps_time' in data
        assert 'teltrg_time_by_type' in data


def test_2100():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelEvent, SimTelTrackEvent

    with EventIOFile(test_file) as f:

        # search for first event
        o = find_type(f, SimTelEvent)
        s = find_type(o, SimTelTrackEvent)

        pointing = s.parse_data_field()
        assert 'azimuth_raw' in pointing.dtype.names
        assert 'altitude_raw' in pointing.dtype.names


def test_2200():
    from eventio.simtel.objects import SimTelTelEvent

    assert SimTelTelEvent.type_to_telid(3305) == 205
    assert SimTelTelEvent.type_to_telid(3205) == 105
    assert SimTelTelEvent.type_to_telid(2203) == 3

@pytest.mark.xfail
def test_2010():
    assert False

@pytest.mark.xfail
def test_2011():
    assert False

@pytest.mark.xfail
def test_2012():
    assert False

@pytest.mark.xfail
def test_2013():
    assert False

@pytest.mark.xfail
def test_2014():
    assert False

@pytest.mark.xfail
def test_2015():
    assert False

@pytest.mark.xfail
def test_2016():
    assert False

@pytest.mark.xfail
def test_2017():
    assert False

@pytest.mark.xfail
def test_2018():
    assert False

@pytest.mark.xfail
def test_2019():
    assert False

@pytest.mark.xfail
def test_2020():
    assert False


def test_2021():
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


def test_2022():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelMoni

    with EventIOFile(test_file) as f:
        all_2022_obs = [
            o for o in f
            if o.header.type == SimTelTelMoni.eventio_type
        ]

        for i, o in enumerate(all_2022_obs):
            d = o.parse_data_field()
            bytes_not_consumed = o.read()
            # assert parse_data_field() consumed nearly all data,
            # and all bytes which are not consumed are zero
            # DN: testing this manually resulted always in 1 byte not
            #     being consumed.
            assert len(bytes_not_consumed) < 4
            for byte_ in bytes_not_consumed:
                assert byte_ == 0

            assert d['telescope_id'] == i + 1

            # print(d)
            # Looks reasonable
            '''
            {
                'status_time': (1408549473, 35597000),
                'trig_time': (1408549473, 35597000),
                'ped_noise_time': (1408549473, 35597000),
                'hv_temp_time': (1408549473, 35597000),
                'dc_rate_time': (1408549473, 35597000),
                'hv_thr_time': (1408549473, 35597000),
                'set_daq_time': (1408549473, 35597000),
                'status_bits': 4778,
                'coinc_count': 0,
                'event_count': 0,
                'trigger_rate': 750.0,
                'sector_rate': array([34.910618, 26.935232, 34.35181 , ..., 38.751358, 28.185534, 33.873787], dtype=float32),
                'event_rate': 700.0,
                'data_rate': 1.2999999523162842,
                'mean_significant': 0.0,
                'num_ped_slices': 30,
                'pedestal': array([[2979.467 , 3009.359 , 3010.3691, ..., 2990.7085, 2929.3687, 2981.3044]], dtype=float32),
                'noise': array([[5.477226, 5.477226, 5.477226, ..., 5.477226, 5.477226, 5.477226]], dtype=float32),
                'num_drawer_temp': 0,
                'num_camera_temp': 0,
                'hv_v_mon': array([836, 814, 823, ..., 893, 858, 847], dtype=int16),
                'hv_i_mon': array([118, 114, 116, ..., 126, 121, 119], dtype=int16),
                'hv_stat': array([1, 1, 1, ..., 1, 1, 1], dtype=uint8),
                'drawer_temp': array([], shape=(116, 0), dtype=int16),
                'camera_temp': array([], dtype=int16),
                'current': array([18, 19, 19, ..., 18, 18, 19], dtype=uint16),
                'scaler': array([201, 201, 201, ..., 201, 201, 201], dtype=uint16),
                'hv_dac': array([ 983,  958,  968, ..., 1051, 1009,  997], dtype=uint16),
                'thresh_dac': array([
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870, 6870,
                   6870, 6870, 6870, 6870, 6870, 6870], dtype=uint16),
                'hv_set': array([1, 1, 1, ..., 1, 1, 1], dtype=uint8),
                'trig_set': array([1, 1, 1, ..., 1, 1, 1], dtype=uint8),
                'daq_conf': 1,
                'daq_scaler_win': 0,
                'daq_nd': 0,
                'daq_acc': 0,
                'daq_nl': 30
            }
            '''


def test_2023():
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
    'lascal_id': 2,
    'max_int_frac': array([0.], dtype=float32),
    'max_pixtm_frac': array([0.], dtype=float32),
    'calib': array([[0.02838226, 0.02617863, 0.02520496, ..., 0.02812363, 0.02769747, 0.02691549]], dtype=float32),
    'tm_calib': array([[-21.383808, -21.283247, -21.452444, ..., -22.023653, -21.650948, -21.601557]], dtype=float32)}
    '''

@pytest.mark.xfail
def test_2024():
    assert False

@pytest.mark.xfail
def test_2025():
    assert False


def test_2026():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelMCPeSum

    with EventIOFile(test_file) as f:
        all_2026_obs = [
            o for o in f
            if o.header.type == SimTelMCPeSum.eventio_type
        ]

        for i, o in enumerate(all_2026_obs):
            d = o.parse_data_field()
            bytes_not_consumed = o.read()
            # assert parse_data_field() consumed all data,
            assert len(bytes_not_consumed) == 0

            assert d['event'] // 100 == d['shower_num']

@pytest.mark.xfail
def test_2027():
    assert False

@pytest.mark.xfail
def test_2028():
    assert False

