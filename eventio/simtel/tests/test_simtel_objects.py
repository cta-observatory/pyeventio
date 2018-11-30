from pkg_resources import resource_filename
import pytest
from pytest import approx
import numpy as np

from eventio.search_utils import (
    find_type,
    collect_toplevel_of_type,
    find_all_subobjects,
)

prod2_file = resource_filename('eventio', 'resources/gamma_test.simtel.gz')
prod4b_sst1m_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'
)
prod4b_astri_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'
)

expected_adc_samples_event1_tel_id_38 = np.load(
    resource_filename(
        'eventio',
        'resources/gamma_test.simtel_event1_tel_id_38_adc_samples.npy'
    )
)


def test_70():
    from eventio import EventIOFile
    from eventio.simtel.objects import History

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
        classes_under_test = collect_toplevel_of_type(f, SimTelRunHeader)

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

    with EventIOFile(prod2_file) as f:
        o = find_type(f, SimTelRunHeader)

        data = o.parse_data_field()
        assert data['observer'] == b'bernlohr@lfc371.mpi-hd.mpg.de'
        assert data['target'] == b'Monte Carlo beach'


def test_2001():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelMCRunHeader

    with EventIOFile(prod2_file) as f:
        classes_under_test = collect_toplevel_of_type(f, SimTelMCRunHeader)

        for o in classes_under_test:
            d = o.parse_data_field()
            assert d

            bytes_not_consumed = o.read()
            # DN: I do not know why two bytes, did not x-check
            assert len(bytes_not_consumed) == 0
            for byte_ in bytes_not_consumed:
                assert byte_ == 0


def test_2002_v3():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamSettings

    with EventIOFile(prod2_file) as f:
        obj = find_type(f, SimTelCamSettings)

        assert obj.header.version == 3

        # values from pyhessio
        camera_data = obj.parse_data_field()
        assert camera_data['telescope_id'] == 1
        assert camera_data['n_pixels'] == 1855
        assert camera_data['focal_length'] == np.float32(28.0)
        assert len(camera_data['pixel_x']) == 1855
        assert len(camera_data['pixel_y']) == 1855
        assert camera_data['pixel_x'][1] == np.float32(0.05)
        assert camera_data['pixel_x'][2] == np.float32(0.025)
        assert np.all(camera_data['pixel_shape'] == -1)
        assert camera_data['n_mirrors'] == 198
        assert camera_data['cam_rot'] == 0.1901187151670456


def test_2002_v5():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamSettings

    with EventIOFile(prod4b_astri_file) as f:
        obj = find_type(f, SimTelCamSettings)

        assert obj.header.version == 5
        cam_data = obj.parse_data_field()
        assert cam_data['n_pixels'] == 2368  # astri
        assert 'effective_focal_length' in cam_data


def test_2003():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamOrgan

    with EventIOFile(prod2_file) as f:
        classes_under_test = collect_toplevel_of_type(f, SimTelCamOrgan)

        for class_index, o in enumerate(classes_under_test):
            d = o.parse_data_field()
            assert d

            bytes_not_consumed = o.read()
            # DN: sometimes 1 sometimes 0 ...
            assert len(bytes_not_consumed) <= 1
            for byte_ in bytes_not_consumed:
                assert byte_ == 0

            assert d['telescope_id'] == class_index + 1
            # print(d)
            for pixel_id, sector in enumerate(d['sectors']):
                # sector must never contain a zero, unless it is in the
                # very first element
                assert (sector[1:] == 0).sum() == 0
                # print(pixel_id, sector)


def test_2004():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelset

    with EventIOFile(prod2_file) as f:
        o = find_type(f, SimTelPixelset)

        assert o.telescope_id == 1
        pixelset = o.parse_data_field()

        assert pixelset['num_pixels'] == 1855


def test_2005():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelDisable

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
        o = find_type(f, SimTelEvent)
        s = find_type(o, SimTelCentEvent)

        data = s.parse_data_field()
        assert 'cpu_time' in data
        assert 'gps_time' in data
        assert 'teltrg_time_by_type' in data


def test_2100():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelEvent, SimTelTrackEvent

    with EventIOFile(prod2_file) as f:

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


def test_2010():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCentEvent
    # class under test
    from eventio.simtel.objects import SimTelEvent

    with EventIOFile(prod2_file) as f:
        events = collect_toplevel_of_type(f, SimTelEvent)
        for event in events:
            assert isinstance(next(event), SimTelCentEvent)


def test_2011():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelEvent, SimTelEvent
    # class under test
    from eventio.simtel.objects import SimTelTelEvtHead

    with EventIOFile(prod2_file) as f:
        all_2011_obs = find_all_subobjects(
            f,
            [SimTelEvent, SimTelTelEvent, SimTelTelEvtHead]
        )

        for i, o in enumerate(all_2011_obs):
            o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            bytes_not_consumed = o.read()
            assert len(bytes_not_consumed) <= 4
            for byte_ in bytes_not_consumed:
                assert byte_ == 0

            # print(d)
        # a few printed examples: only version 1!!
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


def test_2012():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelEvent, SimTelEvent
    # class under test
    from eventio.simtel.objects import SimTelTelADCSum

    with EventIOFile(prod4b_astri_file) as f:
        # find class under test in the deep hierarchy jungle
        # would be nice to find an easier way for this.
        all_adc_sums = find_all_subobjects(
            f, [SimTelEvent, SimTelTelEvent, SimTelTelADCSum]
        )

        for o in all_adc_sums:
            o.parse_data_field()


def test_2013():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelEvent, SimTelEvent
    # class under test
    from eventio.simtel.objects import SimTelTelADCSamp

    with EventIOFile(prod2_file) as f:
        all_2013_obs = find_all_subobjects(
            f,
            [SimTelEvent, SimTelTelEvent, SimTelTelADCSamp]
        )[:3]  # <--- reduce number of containers to speed up test

        assert all_2013_obs
        print(
            '{} objects of type 2013 found, parsing ... '
            .format(
                len(all_2013_obs)
            )
        )

        event1_tel_38 = all_2013_obs[0]
        assert event1_tel_38.telescope_id == 38

        event1_tel_38_adc_samples = event1_tel_38.parse_data_field()
        assert (
            event1_tel_38_adc_samples.shape ==
            expected_adc_samples_event1_tel_id_38.shape
        )
        assert (
            event1_tel_38_adc_samples ==
            expected_adc_samples_event1_tel_id_38
        ).all()

        # we cannot test all of the 50 objects ... the last is truncated
        for object_index, o in enumerate(all_2013_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            bytes_not_consumed = o.read()
            assert len(bytes_not_consumed) <= 3
            for byte_ in bytes_not_consumed:
                assert byte_ == 0


def test_2014():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelTelEvent, SimTelEvent
    # class under test
    from eventio.simtel.objects import SimTelTelImage

    expected_telescope_ids = [
        38, 47, 11, 21, 24, 26, 61, 63, 118, 119, 17, 104, 124, 2, 4, 14,
        15, 17, 19, 2, 3, 4, 10, 12, 25, 8, 16, 26, 28, 1, 3, 4, 9, 12,
        25, 62, 110, 126, 9, 12, 22, 25, 27, 62
    ]
    print(expected_telescope_ids)

    with EventIOFile(prod2_file) as f:
        all_2014_obs = find_all_subobjects(
            f,
            [SimTelEvent, SimTelTelEvent, SimTelTelImage]
        )

        assert all_2014_obs
        print(
            '{} objects of type 2014 found, parsing ... '
            .format(
                len(all_2014_obs)
            )
        )

        # we cannot test all of the 50 objects ... the last is truncated
        for object_index, o in enumerate(all_2014_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            bytes_not_consumed = o.read()
            assert len(bytes_not_consumed) <= 2
            for byte_ in bytes_not_consumed:
                assert byte_ == 0

            assert d['telescope_id'] == expected_telescope_ids[object_index]


@pytest.mark.xfail
def test_2015():
    # no 2015 in gamma_test
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


def test_2020():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelMCShower

    hessio_data = np.load(resource_filename(
        'eventio', 'resources/gamma_test_mc_shower.npy'
    ))
    with EventIOFile(prod2_file) as f:
        for d, o in zip(hessio_data, filter(lambda o: isinstance(o, SimTelMCShower), f)):
            mc = o.parse_data_field()
            assert mc['primary_id'] == 0
            assert mc['energy'] == d[0]
            assert mc['h_first_int'] == d[1]
            assert mc['xmax'] == d[2]


def test_2021():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelMCEvent

    with EventIOFile(prod2_file) as f:
        all_2021_obs = collect_toplevel_of_type(f, SimTelMCEvent)

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

    with EventIOFile(prod2_file) as f:
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

    with EventIOFile(prod2_file) as f:
        all_2023_obs = [
            o for o in f
            if o.header.type == SimTelLasCal.eventio_type
        ]

        for i, o in enumerate(all_2023_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data from o
            assert len(o.read()) == 0

            assert d['telescope_id'] == i + 1
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

    with EventIOFile(prod2_file) as f:
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


def test_2027():
    # This test does not work with our gamma_prod2_file
    # since it does not contain any object of type 2027
    # :-(
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelList

    with EventIOFile(prod2_file) as f:
        all_2027_obs = [
            o for o in f
            if o.header.type == SimTelPixelList.eventio_type
        ]

        for i, o in enumerate(all_2027_obs):
            d = o.parse_data_field()
            # assert parse_data_field() consumed all data,
            bytes_not_consumed = o.read()
            assert len(bytes_not_consumed) == 0

            assert d


@pytest.mark.xfail
def test_2028():
    assert False
