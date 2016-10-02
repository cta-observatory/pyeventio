import pkg_resources
import eventio
from os import path


def test_tell():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)

    obj = f[1]
    obj.seek(0)

    assert obj.tell() == 0
    obj.read(4)
    assert obj.tell() == 4


def test_seek():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)

    obj = f[1]

    obj.seek(0)
    pos = obj.seek(0, 2)

    assert pos == obj.header.length
