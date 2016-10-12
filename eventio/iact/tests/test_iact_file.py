import eventio
import pkg_resources
from os import path

from pytest import approx, raises


testfile_path = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)
testfile_reuse_path = pkg_resources.resource_filename(
    'eventio', path.join('resources', '3_gammas_reuse_5.dat')
)
testfile_two_telescopes = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'two_telescopes.dat')
)


def test_file_open():
    with open(testfile_path, 'rb') as testfile:
        eventio.IACTFile(testfile)


def test_n_events():
    ''' tests if the number of events in the testfile is 1 '''
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)
        assert len(f.showers) == 1


def test_read_run_header():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        f.run_header
        assert f.run_header.energy_range[0] == approx(5.0)
        assert f.run_header.energy_range[1] == approx(100.0)
        assert f.run_header.energy_slope == approx(-2.7)


def test_run_end_block():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        assert hasattr(f, 'end_block')


def test_read_input_card():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        assert hasattr(f, 'input_card')


def test_read_telescopes():
    with open(testfile_path, 'rb') as testfile:
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
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        event = next(f)


def test_iterating():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        for event in f:
            pass

def test_bunches():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)
        event = next(f)

        columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')

        assert event.photon_bunches.shape == (382, )
        assert event.photon_bunches.dtype.names == columns


def test_bunches_2():
    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')

    f = eventio.IACTFile(testfile_two_telescopes)
    for event in f:
        assert len(event.photon_bunches) == 2
        assert event.photon_bunches[1].dtype.names == columns


def test_event_header():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)
        event = next(f)

        assert hasattr(event, 'header')


def test_event_end_block():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)
        event = next(f)

        assert hasattr(event, 'end_block')


def test_event_with_reuse():
    with open(testfile_reuse_path, 'rb') as testfile:
        f = eventio.IACTFile(testfile)

        assert len(f.showers) == 3
        assert f.n_events == 15
        for i, e in enumerate(f):
            assert e.reuse == (i % 5) + 1
            assert e.shower == (i // 5) + 1
