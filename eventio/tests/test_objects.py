import pkg_resources
import eventio
from os import path

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

def test_level():
    f = eventio.EventIOFile(testfile)

    assert f[0].header.level == 0
    assert f[5][0].header.level == 1
