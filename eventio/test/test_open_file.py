import eventio
from os import path

def test_is_install_folder_a_directory():
    dir_ = path.dirname(eventio.__file__)
    assert path.isdir(dir_)

def test_can_find_resource_folder():
    dir_ = path.join(
        path.dirname(eventio.__file__),
        'resources')
    assert path.isdir(dir_)

def test_can_find_one_shower_dat():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    assert path.isfile(p)

def test_can_open_file():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    eventio.EventIoFile(p)

def test_can_open_file():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    eventio.EventIoFile(p)

def test_file_has_run_header():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    f = eventio.EventIoFile(p)
    f.run_header

def test_file_is_iterable():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    f = eventio.EventIoFile(p)
    for event in f:
        pass

def test_file_has_at_least_one_event():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    f = eventio.EventIoFile(p)
    event = next(f)
    assert isinstance(event, eventio.photonbunches.PhotonBundle)

def test_event_has_382_bunches():
    p = path.join(
        path.dirname(eventio.__file__),
        'resources',
        'one_shower.dat')
    f = eventio.EventIoFile(p)
    event = next(f)
    assert event.header.n_bunches == 382

