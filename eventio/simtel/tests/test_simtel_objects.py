from pkg_resources import resource_filename


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


def test_pixelset():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelPixelset

    with EventIOFile(test_file) as f:
        o = find_type(f, SimTelPixelset)

        assert o.telescope_id == 1
        pixelset = o.parse_data_field()

        assert pixelset['num_pixels'] == 1855
