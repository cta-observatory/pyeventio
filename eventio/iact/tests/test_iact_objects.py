import eventio
import pkg_resources
from os import path

from pytest import approx

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

prod4_simtel = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz')
)


def test_photo_electrons():
    from eventio import EventIOFile
    from eventio.iact import PhotoElectrons
    from eventio.search_utils import yield_n_subobjects

    with EventIOFile(prod4_simtel) as f:
        for o in yield_n_subobjects(f, PhotoElectrons):
            o.parse()
            not_read = o.read()
            assert len(not_read) == 0 or all(b == 0 for b in not_read)


def test_file_has_run_header():
    from eventio.iact import RunHeader
    with eventio.EventIOFile(testfile) as f:
        obj = next(f)
        assert isinstance(obj, RunHeader)


def test_read_run_header():
    with eventio.EventIOFile(testfile) as f:
        run_header = next(f).parse()

        assert run_header.energy_range[0] == approx(5.0)
        assert run_header.energy_range[1] == approx(100.0)
        assert run_header.energy_slope == approx(-2.7)


def test_telescope_definition():
    from eventio.iact import TelescopeDefinition

    with eventio.EventIOFile(testfile) as f:
        next(f) # skip run_header
        next(f) # skip inputcard

        telescope_definition = next(f)
        assert isinstance(telescope_definition, TelescopeDefinition)
        assert telescope_definition.n_telescopes == 1

        telescope_definition_data = telescope_definition.parse()
        assert telescope_definition_data['x'][0] == approx(0.0)
        assert telescope_definition_data['y'][0] == approx(0.0)
        assert telescope_definition_data['z'][0] == approx(2500.0)
        assert telescope_definition_data['r'][0] == approx(2500.0)


def test_corsika_event_header():
    from eventio.iact import EventHeader
    with eventio.EventIOFile(testfile) as f:
        # first event header should be the 4th object in the file
        for i in range(4):
            obj = next(f)

        assert isinstance(obj, EventHeader)
        event_header = obj.parse()
        assert event_header.event_id == 1
        assert event_header.zenith_angle == approx(0.0)
        assert event_header.azimuth_angle == approx(0.0)
        assert event_header.total_energy == approx(9.3249321)


def test_corsika_array_offsets():
    from eventio.iact import ArrayOffsets
    with eventio.EventIOFile(testfile) as f:
        # first array offset object should be the 5th object in the file
        for i in range(5):
            obj = next(f)

        assert isinstance(obj, ArrayOffsets)
        assert obj.n_arrays == 1

        offsets = obj.parse()
        assert offsets['x'][0] == approx(-506.9717102050781)
        assert offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    from eventio.iact import Photons, TelescopeData
    with eventio.EventIOFile(testfile) as f:
        # first telescope data  object should be the 6th object in the file
        for i in range(6):
            obj = next(f)

        assert isinstance(obj, TelescopeData)
        photons = next(obj)
        assert isinstance(photons, Photons)
        assert photons.n_bunches == 382


def test_bunches():
    from eventio.iact import TelescopeData

    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')
    with eventio.EventIOFile(testfile) as f:
        # first telescope data  object should be the 6th object in the file
        for i in range(6):
            obj = next(f)

        assert isinstance(obj, TelescopeData)
        photons = next(obj)
        bunches = photons.parse()

        assert bunches.dtype.names == columns
