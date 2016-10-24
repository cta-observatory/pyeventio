import eventio
import pkg_resources
from os import path

from pytest import approx, raises


testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)
testfile_reuse = pkg_resources.resource_filename(
    'eventio', path.join('resources', '3_gammas_reuse_5.dat')
)
testfile_two_telescopes = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'two_telescopes.dat')
)


def test_file_open():
    eventio.IACTFile(testfile)


def test_n_events():
    ''' tests if the number of events in the testfile is 1 '''
    f = eventio.IACTFile(testfile)
    assert len(f) == 1


def test_read_run_header():
    f = eventio.IACTFile(testfile)

    assert hasattr(f, 'header')
    assert f.header.energy_range[0] == approx(5.0)
    assert f.header.energy_range[1] == approx(100.0)
    assert f.header.energy_slope == approx(-2.7)


def test_run_end_block():
    f = eventio.IACTFile(testfile)
    assert hasattr(f, 'end_block')


def test_read_input_card():
    f = eventio.IACTFile(testfile)

    assert hasattr(f, 'input_card')


def test_read_telescopes():
    f = eventio.IACTFile(testfile)

    assert f.n_telescopes == 1
    assert hasattr(f, 'telescope_positions')
    assert f.telescope_positions['x'][0] == approx(0)


def test_read_telescopes_2():
    f = eventio.IACTFile(testfile_two_telescopes)

    assert f.n_telescopes == 2
    assert hasattr(f, 'telescope_positions')
    assert f.telescope_positions['x'][1] == approx(5000)


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

    assert event.photon_bunches[0].shape == (382, )
    assert event.photon_bunches[0].dtype.names == columns


def test_bunches_2():
    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')

    f = eventio.IACTFile(testfile_two_telescopes)
    for event in f:
        assert len(event.photon_bunches) == 2
        assert event.photon_bunches[1].dtype.names == columns


def test_event_header():
    f = eventio.IACTFile(testfile)
    event = f[0]

    assert hasattr(event, 'header')
    assert event.header.event_id == 1
    assert event.header.zenith_angle == approx(0.0)
    assert event.header.azimuth_angle == approx(0.0)
    assert event.header.total_energy == approx(9.3249321)


def test_event_end_block():
    f = eventio.IACTFile(testfile)
    event = f[0]

    assert hasattr(event, 'end_block')


def test_event_with_reuse():
    f = eventio.IACTFile(testfile_reuse)
    assert f.n_events == 15
    assert f.n_showers == 3
    for i, e in enumerate(f):
        assert e.event_number == i
        assert e.reuse == (i % 5) + 1
