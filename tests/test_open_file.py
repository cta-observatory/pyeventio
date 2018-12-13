import eventio
from os import path
import pkg_resources


def test_is_install_folder_a_directory():
    dir_ = path.dirname(eventio.__file__)
    assert path.isdir(dir_)


def test_can_open_file():
    testfile = 'tests/resources/one_shower.dat'
    eventio.EventIOFile(testfile)


def test_file_is_iterable():
    testfile = 'tests/resources/one_shower.dat'
    f = eventio.EventIOFile(testfile)
    for event in f:
        pass


def test_file_has_correct_types():
    testfile = 'tests/resources/one_shower.dat'
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]


def test_types_gzipped():
    testfile = 'tests/resources/one_shower.dat'
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]
