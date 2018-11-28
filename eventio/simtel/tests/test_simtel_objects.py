from pkg_resources import resource_filename


test_file = resource_filename('eventio', 'resources/gamma_test.simtel.gz')


def test_run_heder():
    from eventio import EventIOFile
    from eventio.simtel import SimTelRunHeader

    with EventIOFile(test_file) as f:
        o = next(f)
        while not isinstance(o, SimTelRunHeader):
            o = next(f)

        data = o.parse_data_field()
        data['observer'] = b'bernlohr@lfc371.mpi-hd.mpg.de'
        data['target'] = b'Monte Carlo beach'


def test_2002():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamSettings

    with EventIOFile(test_file) as f:
        obj = next(f)
        while obj.header.type != SimTelCamSettings.eventio_type:
            obj = next(f)

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
        o = next(f)
        while o.eventio_type != SimTelEvent.eventio_type:
            o = next(f)

        for s in o:
            if isinstance(s, SimTelTrackEvent):
                break
        else:
            assert False, 'No Track event found'

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