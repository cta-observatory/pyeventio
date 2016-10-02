import eventio
import pkg_resources
from os import path

from pytest import approx


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

    assert run_header['energy range'][0] == approx(5.0)
    assert run_header['energy range'][1] == approx(100.0)
    assert run_header['slope of energy spectrum'] == approx(-2.7)


def test_telescope_definition():
    from eventio.iact import CorsikaTelescopeDefinition
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    telescope_definition = f[2]
    assert isinstance(telescope_definition, CorsikaTelescopeDefinition)
    assert telescope_definition.num_telescopes == 1
    assert telescope_definition['x'][0] == approx(0.0)
    assert telescope_definition['y'][0] == approx(0.0)
    assert telescope_definition['z'][0] == approx(2500.0)
    assert telescope_definition['r'][0] == approx(2500.0)


def test_corsica_event_header():
    from eventio.iact import CorsikaEventHeader
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    event_header = f[3]

    assert isinstance(event_header, CorsikaEventHeader)
    assert event_header['event number'] == 1
    assert event_header['angle in radian: (zenith, azimuth)'][0] == approx(0.0)
    assert event_header['angle in radian: (zenith, azimuth)'][1] == approx(0.0)
    assert event_header['total energy in GeV'] == approx(9.3249321)


def test_corsica_telescope_offsets():
    from eventio.iact import CorsikaTelescopeOffsets
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    offsets = f[4]

    assert isinstance(offsets, CorsikaTelescopeOffsets)
    assert offsets.n_offsets == 1
    assert offsets['x'][0] == approx(-506.9717102050781)
    assert offsets['y'][0] == approx(-3876.447265625)


def test_event_has_382_bunches():
    from eventio.iact import IACTPhotons
    testfile = pkg_resources.resource_filename(
        'eventio', path.join('resources', 'one_shower.dat')
    )
    f = eventio.EventIOFile(testfile)
    photons = f[5][0]
    assert isinstance(photons, IACTPhotons)
    assert photons.n_bunches == 382
