import eventio
import pkg_resources
from os import path

from pytest import approx
import eventio.iact.objects as objects

testfile_path = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

def test_corsica_event_header():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        event_header = objects.make_CorsikaEventHeader(f[3])

        assert event_header.event_id == 1
        assert event_header.zenith_angle == approx(0.0)
        assert event_header.azimuth_angle == approx(0.0)
        assert event_header.total_energy == approx(9.3249321)



def test_telescope_definition():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        telescope_definition = objects.make_CorsikaTelescopeDefinition(f[2])

        assert telescope_definition.n_telescopes == 1
        assert telescope_definition.tel_pos['x'][0] == approx(0.0)
        assert telescope_definition.tel_pos['y'][0] == approx(0.0)
        assert telescope_definition.tel_pos['z'][0] == approx(2500.0)
        assert telescope_definition.tel_pos['r'][0] == approx(2500.0)



def test_corsica_array_offsets():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        offsets_object = objects.make_CorsikaArrayOffsets(f[4])

        assert len(offsets_object.offsets) == 1
        assert offsets_object.offsets['x'][0] == approx(-506.9717102050781)
        assert offsets_object.offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        telescope_events = objects.make_TelescopeEvents(f[5])
        assert len(telescope_events) == 1

        bunches = telescope_events[0]
        assert len(bunches) == 382


def test_bunches():
    with open(testfile_path, 'rb') as testfile:
        f = eventio.object_tree(testfile)
        telescope_events = objects.make_TelescopeEvents(f[5])
        assert len(telescope_events) == 1

        bunches = telescope_events[0]
        columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')
        assert bunches.dtype.names == columns
