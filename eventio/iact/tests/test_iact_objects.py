import eventio
import pkg_resources
from os import path

from pytest import approx

testfile_path = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

def test_corsica_event_header():
    from eventio.iact.parse_corsika_data import CorsikaEventHeader
    from eventio.iact.objects import parse_eventio_object

    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        event_header = parse_eventio_object(f[3])

        assert event_header.event_id == 1
        assert event_header.zenith_angle == approx(0.0)
        assert event_header.azimuth_angle == approx(0.0)
        assert event_header.total_energy == approx(9.3249321)



def test_telescope_definition():
    from eventio.iact.objects import parse_eventio_object
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        telescope_definition = parse_eventio_object(f[2])

        assert telescope_definition.n_telescopes == 1
        assert telescope_definition.tel_pos['x'][0] == approx(0.0)
        assert telescope_definition.tel_pos['y'][0] == approx(0.0)
        assert telescope_definition.tel_pos['z'][0] == approx(2500.0)
        assert telescope_definition.tel_pos['r'][0] == approx(2500.0)



def test_corsica_array_offsets():
    from eventio.iact.objects import parse_eventio_object
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        offsets_object = parse_eventio_object(f[4])

        assert len(offsets_object.offsets) == 1
        assert offsets_object.offsets['x'][0] == approx(-506.9717102050781)
        assert offsets_object.offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    from eventio.iact.objects import parse_eventio_object
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        bunches = parse_eventio_object(f[5])

        assert len(bunches) == 382


def test_bunches():
    from eventio.iact.objects import parse_eventio_object
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        bunches = parse_eventio_object(f[5])

        columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')
        assert bunches.dtype.names == columns
