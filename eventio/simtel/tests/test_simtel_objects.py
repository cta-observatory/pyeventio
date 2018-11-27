












def test_telid():
    from eventio.simtel.objects import SimTelTelEvent

    assert SimTelTelEvent.type_to_telid(3305) == 205
    assert SimTelTelEvent.type_to_telid(3205) == 105
    assert SimTelTelEvent.type_to_telid(2203) == 3
