import eventio
import pkg_resources
from os import path

from pytest import approx, raises


testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)


def test_file_open():
    eventio.IACTFile(testfile)


def test_num_events():
    ''' tests if the number of events in the testfile is 1 '''
    f = eventio.IACTFile(testfile)
    assert len(f) == 1


def test_read_run_header():
    f = eventio.IACTFile(testfile)

    assert hasattr(f, 'header')
    assert f.header['energy range'][0] == approx(5.0)
    assert f.header['energy range'][1] == approx(100.0)
    assert f.header['slope of energy spectrum'] == approx(-2.7)


def test_run_end_block():
    f = eventio.IACTFile(testfile)
    assert hasattr(f, 'end_block')


def test_read_input_card():
    f = eventio.IACTFile(testfile)

    assert hasattr(f, 'input_card')


def test_get_item():
    f = eventio.IACTFile(testfile)

    event = f[0]
    assert isinstance(event, eventio.iact.CorsikaEvent)


def test_iterating():
    f = eventio.IACTFile(testfile)

    for event in f:
        assert isinstance(event, eventio.iact.CorsikaEvent)


def test_bunches():
    f = eventio.IACTFile(testfile)

    event = f[0]

    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')

    assert event.photon_bunches.shape == (382, )
    assert event.photon_bunches.dtype.names == columns


def test_event_header():
    f = eventio.IACTFile(testfile)
    event = f[0]

    assert hasattr(event, 'header')
    assert event.header['event number'] == 1
    assert event.header['angle in radian: (zenith, azimuth)'][0] == approx(0.0)
    assert event.header['angle in radian: (zenith, azimuth)'][1] == approx(0.0)
    assert event.header['total energy in GeV'] == approx(9.3249321)


def test_event_end_block():
    f = eventio.IACTFile(testfile)
    event = f[0]

    assert hasattr(event, 'end_block')
