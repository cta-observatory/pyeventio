import eventio

testfile = 'tests/resources/one_shower.dat'


def test_tell():
    with eventio.EventIOFile(testfile) as f:
        obj = next(f)
        obj.seek(0)

        assert obj.tell() == 0
        obj.read(4)
        assert obj.tell() == 4


def test_seek():
    with eventio.EventIOFile(testfile) as f:
        obj = next(f)

        obj.seek(0)
        pos = obj.seek(0, 2)

        assert pos == obj.header.content_size
