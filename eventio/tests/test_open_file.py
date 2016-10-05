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
    testfile_path = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    with open(testfile_path, 'rb') as testfile:
        eventio.objects(testfile)


def test_can_open_file():
    testfile_path = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    with open(testfile_path, 'rb') as testfile:
        f = eventio.objects(testfile)
        for event in f:
            pass

def test_file_has_correct_types():
    testfile_path = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    with open(testfile_path, 'rb') as testfile:
        types = [ tuple(h.type for h in obj.headers) for obj in eventio.objects(testfile)]
        assert types == [(1200,), (1212,), (1201,), (1202,), (1203,), (1204, 1205), (1209,), (1210,)]


def test_types_gzipped():
    import gzip
    testfile_path = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat.gz')
    )
    with gzip.GzipFile(testfile_path, 'rb') as testfile:
        types = [ tuple(h.type for h in obj.headers) for obj in eventio.objects(testfile)]
        assert types == [(1200,), (1212,), (1201,), (1202,), (1203,), (1204, 1205), (1209,), (1210,)]
        