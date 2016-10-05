import eventio
from os import path
import pkg_resources


def test_is_install_folder_a_directory():
    dir_ = path.dirname(eventio.__file__)
    assert path.isdir(dir_)


def test_can_find_resource_folder():
    assert pkg_resources.resource_isdir('eventio', 'resources')


def test_can_find_one_shower_dat():
    assert pkg_resources.resource_exists(
        'eventio', path.join('resources', 'one_shower.dat')
    )


def test_can_open_file():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    eventio.EventIOFile(testfile)


def test_file_is_iterable():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    for event in f:
        pass


def test_file_has_correct_types():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]


def test_types_gzipped():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat.gz')
    )
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]
