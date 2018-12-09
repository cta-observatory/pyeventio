import pytest
import os
import pkg_resources
from pytest import importorskip
from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first

prod2_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_test.simtel.gz')
)

prod4b_astri_file = pkg_resources.resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'
)

prod4b_corsika = pkg_resources.resource_filename(
    'eventio',
    'resources/run102_gamma_za20deg_azm0deg-paranal-sst.corsika.zst'
)


simple_corsika = pkg_resources.resource_filename(
    'eventio',
    'resources/one_shower.dat'
)


def test_reprs_prod2():
    # for scripts/print_structure.py the reprs must work
    # therefore this test is here

    # gamma_test is truncated, so this should raise
    with pytest.raises(EOFError):
        with EventIOFile(prod2_path) as file_:
            for obj in yield_all_objects_depth_first(file_):
                assert repr(obj)


def test_reprs_prod4():
    from eventio import EventIOFile

    with EventIOFile(prod4b_astri_file) as f:
        for i, obj in enumerate(yield_all_objects_depth_first(f)):
            repr(obj)


def test_reprs_corsika():
    from eventio import EventIOFile

    with EventIOFile(simple_corsika) as f:
        for i, obj in enumerate(yield_all_objects_depth_first(f)):
            repr(obj)


def test_reprs_prod4_corsika():
    importorskip('zstandard')
    from eventio import EventIOFile

    with EventIOFile(prod4b_corsika) as f:
        for i, obj in enumerate(yield_all_objects_depth_first(f)):
            repr(obj)
