import eventio
from os import path
from itertools import zip_longest


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


def test_file_has_objects_at_expected_position():
    expected = [
        (16, 1096),
        (1128, 448),
        (1592, 20),
        (1628, 1096),
        (2740, 16),
        (2772, 6136),
        (8924, 1096),
        (10036, 16),
    ]
    testfile = 'tests/resources/one_shower.dat'
    f = eventio.EventIOFile(testfile)

    for o, (addr, size) in zip_longest(f, expected):
        assert o.header.content_address == addr
        assert o.header.content_size == size


def test_file_has_correct_types():
    testfile = 'tests/resources/one_shower.dat'
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]


def test_types_gzip():
    testfile = 'tests/resources/one_shower.dat.gz'
    f = eventio.EventIOFile(testfile, zcat=False)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]


def test_types_zcat():
    from eventio.base import PipeWrapper
    testfile = 'tests/resources/one_shower.dat.gz'
    f = eventio.EventIOFile(testfile)

    assert isinstance(f._filehandle, PipeWrapper)
    types = [o.header.type for o in f]
    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]
