def test_repr():
    from eventio import EventIOFile

    e = EventIOFile('tests/resources/gamma_test.simtel.gz')
    o = next(e)
    assert repr(o.header)
