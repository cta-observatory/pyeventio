
import gzip
import tempfile
import pkg_resources
import os
import pytest

from eventio.simtel.simtelfile import SimTelFile

prod2_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_test.simtel.gz')
)

prod3_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_test_large_truncated.simtel.gz')
)

prod4_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz')
)

# using a zstd file ensures SimTelFile is not seeking back, when reading
# a file
prod4_zst_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.zst')
)


test_paths = [prod2_path, prod3_path, prod4_path, prod4_zst_path]

def test_can_open():
    for path in test_paths:
        assert SimTelFile(path)

def test_at_least_one_event_found():
    for path in test_paths:
        one_found = False
        for event in SimTelFile(path):
            one_found = True
            break
        assert one_found, path


def test_iterate_complete_file():
    expected_counter_values = {
        prod2_path: 8,
        prod3_path: 5,
        prod4_path: 28,
        prod4_zst_path: 28,  # the same of course
    }
    for path in test_paths:
        try:
            for counter, event in enumerate(SimTelFile(path)):
                pass
        except (EOFError, IndexError):  # truncated files might raise these...
            pass
        assert counter == expected_counter_values[path]
