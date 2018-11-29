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


def test_2022_all():
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
    'lascal_id': 2,
    'max_int_frac': array([0.], dtype=float32),
    'max_pixtm_frac': array([0.], dtype=float32),
    'calib': array([[0.02838226, 0.02617863, 0.02520496, ..., 0.02812363, 0.02769747, 0.02691549]], dtype=float32),
    'tm_calib': array([[-21.383808, -21.283247, -21.452444, ..., -22.023653, -21.650948, -21.601557]], dtype=float32)}
    '''


def test_2011_all():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelEvent, SimTelEvent
    # class under test
    from eventio.simtel.objects import SimTelTelEvtHead


    with EventIOFile(test_file) as f:
        all_2011_obs = []

        # find class under test in the deep hierarchy jungle
        # would be nice to find an easier way for this.
        for o in f:
            if isinstance(o, SimTelEvent):
                for sub in o:
                    if isinstance(sub, SimTelTelEvent):
                        for subsub in sub:
                            if isinstance(subsub, SimTelTelEvtHead):
                                all_2011_obs.append(subsub)


        for i, o in enumerate(all_2011_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            bytes_not_consumed = o.read()
            assert len(bytes_not_consumed) <= 4
            for byte_ in bytes_not_consumed:
                assert byte_ == 0


        # a few printed examples: only version 1!!
        # print(d)
        '''
        {
            'loc_count': 1,
            'glob_count': 408,
            'cpu_time': (1408549473, 35597000),
            'gps_time': (0, 0),
            '_t': 1281, # <-- 0x501
             'trg_source': 1,
            'list_trgsect': array([174, 175, 198, 199], dtype=int16),
            'time_trgsect': array(
                [37.537537, 37.537537, 37.537537, 37.537537],
                dtype=float32
            )
        }
        {
            'loc_count': 1,
            'glob_count': 408,
            'cpu_time': (1408549473, 35597000),
            'gps_time': (0, 0),
            '_t': 1281,
            'trg_source': 1,
            'list_trgsect': array(
                [316, 317, 318, 340, 341, 342], dtype=int16),
            'time_trgsect': array(
                [35.285286, 35.285286, 35.285286,
                35.285286, 35.285286, 35.285286],
                dtype=float32
            )
        }
        {
            'loc_count': 1,
            'glob_count': 409,
            'cpu_time': (1408549476, 147099000),
            'gps_time': (0, 0),
            '_t': 1281,
            'trg_source': 1,
            'list_trgsect': array(
                [ 501,  742,  743,  744,  745,  748,  964,  974,  975,
                  1955, 1956, 1960, 2019, 2023, 2024, 2028, 2083, 2087,
                  2088, 2143, 2429, 2430, 2434, 2493, 2497, 2498, 2502,
                  2557, 2561, 2562, 2617, 2622],
                dtype=int16
            ),
            'time_trgsect': array(
            [25.5, 27.5, 27.5, 28.5, 28. , 26.5, 30.5, 30.5, 32. , 28. , 28.5,
            28.5, 28.5, 27. , 26.5, 27.5, 27.5, 27.5, 27.5, 30.5, 31. , 29. ,
            29. , 29. , 27. , 27. , 27. , 27. , 27. , 27. , 31. , 31. ],
            dtype=float32)
        }
        {
            'loc_count': 1,
            'glob_count': 409,
            'cpu_time': (1408549476, 147099000),
            'gps_time': (0, 0),
            '_t': 1281,
            'trg_source': 1,
            'list_trgsect': array([2569, 2570], dtype=int16),
            'time_trgsect': array([27., 27.], dtype=float32)
        }
        '''


def test_2026_all():
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
