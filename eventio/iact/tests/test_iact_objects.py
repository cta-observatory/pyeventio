import eventio
import pkg_resources
from os import path

from pytest import approx

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)


def test_file_has_run_header():
    from eventio.iact import CORSIKARunHeader
    with eventio.EventIOFile(testfile) as f:
        obj = next(f)
        assert isinstance(obj, CORSIKARunHeader)


def test_read_run_header():
    with eventio.EventIOFile(testfile) as f:
        run_header = next(f).parse_data_field()

        assert run_header.energy_range[0] == approx(5.0)
        assert run_header.energy_range[1] == approx(100.0)
        assert run_header.energy_slope == approx(-2.7)


def test_telescope_definition():
    from eventio.iact import CORSIKATelescopeDefinition

    with eventio.EventIOFile(testfile) as f:
        next(f) # skip run_header
        next(f) # skip inputcard

        telescope_definition = next(f)
        assert isinstance(telescope_definition, CORSIKATelescopeDefinition)
        assert telescope_definition.n_telescopes == 1

        telescope_definition_data = telescope_definition.parse_data_field()
        assert telescope_definition_data['x'][0] == approx(0.0)
        assert telescope_definition_data['y'][0] == approx(0.0)
        assert telescope_definition_data['z'][0] == approx(2500.0)
        assert telescope_definition_data['r'][0] == approx(2500.0)


def test_corsika_event_header():
    from eventio.iact import CORSIKAEventHeader
    with eventio.EventIOFile(testfile) as f:
        # first event header should be the 4th object in the file
        for i in range(4):
            obj = next(f)

        assert isinstance(obj, CORSIKAEventHeader)
        event_header = obj.parse_data_field()
        assert event_header.event_id == 1
        assert event_header.zenith_angle == approx(0.0)
        assert event_header.azimuth_angle == approx(0.0)
        assert event_header.total_energy == approx(9.3249321)


def test_corsika_array_offsets():
    from eventio.iact import CORSIKAArrayOffsets
    with eventio.EventIOFile(testfile) as f:
        # first array offset object should be the 5th object in the file
        for i in range(5):
            obj = next(f)

        assert isinstance(obj, CORSIKAArrayOffsets)
        assert obj.n_arrays == 1

        offsets = obj.parse_data_field()
        assert offsets['x'][0] == approx(-506.9717102050781)
        assert offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    from eventio.iact import IACTPhotons, CORSIKATelescopeData
    with eventio.EventIOFile(testfile) as f:
        # first telescope data  object should be the 6th object in the file
        for i in range(6):
            obj = next(f)

        assert isinstance(obj, CORSIKATelescopeData)
        photons = next(obj)
        assert isinstance(photons, IACTPhotons)
        assert photons.n_bunches == 382


def test_bunches():
    from eventio.iact import CORSIKATelescopeData

    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')
    with eventio.EventIOFile(testfile) as f:
        # first telescope data  object should be the 6th object in the file
        for i in range(6):
            obj = next(f)

        assert isinstance(obj, CORSIKATelescopeData)
        photons = next(obj)
        bunches = photons.parse_data_field()

        assert bunches.dtype.names == columns
