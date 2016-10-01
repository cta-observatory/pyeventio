import eventio
import pkg_resources
from os import path
import numpy as np


def test_file_has_correct_types():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    types = [o.header.type for o in f]

    assert types == [1200, 1212, 1201, 1202, 1203, 1204, 1209, 1210]


def test_file_has_run_header():
    from eventio.iact import CorsikaRunHeader
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    assert isinstance(f[0], CorsikaRunHeader)


def test_read_run_header():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    run_header = f[0]

    assert np.isclose(run_header['energy range'][0], 5.0)
    assert np.isclose(run_header['energy range'][1], 100.0)
    assert np.isclose(run_header['slope of energy spectrum'], -2.7)


def test_file_has_at_least_one_event():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    event = next(f)
    assert isinstance(event, eventio.photonbunches.PhotonBundle)


def test_event_has_382_bunches():
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    event = next(f)
    assert event.header.n_bunches == 382
