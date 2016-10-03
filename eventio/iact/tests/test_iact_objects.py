import eventio
import pkg_resources
from os import path

from pytest import approx

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)


def test_file_has_run_header():
    from eventio.iact import CorsikaRunHeader
    f = eventio.EventIOFile(testfile)
    assert isinstance(f[0], CorsikaRunHeader)


def test_read_run_header():
    f = eventio.EventIOFile(testfile)
    run_header = f[0].parse_data_field()

    assert run_header['energy range'][0] == approx(5.0)
    assert run_header['energy range'][1] == approx(100.0)
    assert run_header['slope of energy spectrum'] == approx(-2.7)


def test_telescope_definition():
    from eventio.iact import CorsikaTelescopeDefinition
    f = eventio.EventIOFile(testfile)
    telescope_definition = f[2]
    assert isinstance(telescope_definition, CorsikaTelescopeDefinition)
    assert telescope_definition.num_telescopes == 1

    telescope_definition_data = telescope_definition.parse_data_field()
    assert telescope_definition_data['x'][0] == approx(0.0)
    assert telescope_definition_data['y'][0] == approx(0.0)
    assert telescope_definition_data['z'][0] == approx(2500.0)
    assert telescope_definition_data['r'][0] == approx(2500.0)


def test_corsica_event_header():
    from eventio.iact import CorsikaEventHeader
    f = eventio.EventIOFile(testfile)
    event_header_object = f[3]

    assert isinstance(event_header_object, CorsikaEventHeader)
    event_header = event_header_object.parse_data_field()
    assert event_header['event number'] == 1
    assert event_header['angle in radian: (zenith, azimuth)'][0] == approx(0.0)
    assert event_header['angle in radian: (zenith, azimuth)'][1] == approx(0.0)
    assert event_header['total energy in GeV'] == approx(9.3249321)


def test_corsica_array_offsets():
    from eventio.iact import CorsikaArrayOffsets
    f = eventio.EventIOFile(testfile)
    offsets_object = f[4]

    assert isinstance(offsets_object, CorsikaArrayOffsets)
    assert offsets_object.num_arrays == 1

    offsets = offsets_object.parse_data_field()
    assert offsets['x'][0] == approx(-506.9717102050781)
    assert offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    from eventio.iact import IACTPhotons
    f = eventio.EventIOFile(testfile)
    photons = f[5][0]
    assert isinstance(photons, IACTPhotons)
    assert photons.n_bunches == 382


def test_bunches():
    f = eventio.EventIOFile(testfile)
    photons = f[5][0]
    bunches = photons.parse_data_field()

    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda', 'scattered')
    assert bunches.dtype.names == columns
