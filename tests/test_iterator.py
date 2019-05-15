from eventio import EventIOFile

testfile = 'tests/resources/one_shower.dat'


def test_iterator():
    f = EventIOFile(testfile)

    # make sure f is an iterator
    assert iter(f) is iter(f)

    # make sure, it does not restart:

    it = iter(f)
    first = next(it)

    for o in it:
        assert o.header.content_address > first.header.content_address
