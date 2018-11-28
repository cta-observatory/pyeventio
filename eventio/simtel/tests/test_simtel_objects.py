from pkg_resources import resource_filename


test_file = resource_filename('eventio', 'resources/gamma_test.simtel.gz')












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
