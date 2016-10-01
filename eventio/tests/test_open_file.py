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
