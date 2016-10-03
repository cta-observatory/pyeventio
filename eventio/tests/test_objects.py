import pkg_resources
import eventio
from os import path

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)


def test_tell():
    f = eventio.EventIOFile(testfile)

    obj = f[1]
    obj.seek(0)

    assert obj.tell() == 0
    obj.read(4)
    assert obj.tell() == 4


def test_seek():
    f = eventio.EventIOFile(testfile)

    obj = f[1]

    obj.seek(0)
    pos = obj.seek(0, 2)

    assert pos == obj.header.length


def test_level():
    f = eventio.EventIOFile(testfile)

    assert f[0].header.level == 0
    assert f[5][0].header.level == 1
