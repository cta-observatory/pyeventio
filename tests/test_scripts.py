import pytest
from pytest import importorskip
from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first
import subprocess as sp
import json
import tempfile
from pathlib import Path

prod2_path = 'tests/resources/gamma_test.simtel.gz'
prod4b_astri_file = 'tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'
prod4b_corsika = 'tests/resources/run102_gamma_za20deg_azm0deg-paranal-sst.corsika.zst'
simple_corsika = 'tests/resources/one_shower.dat'


def run_command(*args):
    result = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')

    if result.returncode != 0:
        raise IOError(f'Running {args} failed, output: \n {result.stdout}')

    return result


def test_print_structure():
    run_command('eventio_print_structure', simple_corsika)


def test_print_simtel_history():
    run_command('eventio_print_simtel_history', prod4b_astri_file)


def test_print_object_information():
    run_command('eventio_print_object_information', prod4b_astri_file)

    result = run_command(
        'eventio_print_object_information', '--json', prod4b_astri_file
    )
    # test if json output is valid
    json.loads(result.stdout)


def test_cut_file():
    with tempfile.NamedTemporaryFile(prefix='eventio_test', suffix='.simtel') as f:

        assert Path(prod4b_astri_file).stat().st_size > 2 * 1024**2
        run_command(
            'eventio_cut_file',
            prod4b_astri_file,
            f.name,
            '2M',
        )

        # test file was cleanly cut off after an eventio object
        for o in EventIOFile(f.name):
            pass

        # test file is no larger than given limit
        assert Path(f.name).stat().st_size < 2 * 1024**2


def test_plot_histograms():
    importorskip('matplotlib')
    with tempfile.TemporaryDirectory(prefix='eventio_test') as d:

        run_command(
            'eventio_plot_histograms',
            prod4b_astri_file,
            '-o', str(Path(d) / 'hist')
        )

        for i in range(1, 11):
            assert (Path(d) / f'hist_{i:03d}.pdf').exists()


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
