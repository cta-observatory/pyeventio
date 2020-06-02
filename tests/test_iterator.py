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


def test_peek():
    f = EventIOFile(testfile)

    o = f.peek()
    assert o is f.peek()  # make sure peek does not advance
    assert o is next(f)   # make sure peek gives us the next object
    assert o is not f.peek()  # assure we get the next
    assert f.peek() is next(f)
