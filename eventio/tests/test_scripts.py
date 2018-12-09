import os
import pkg_resources
from eventio import EventIOFile
from eventio.search_utils import yield_all_objects_depth_first

prod2_path = pkg_resources.resource_filename(
    'eventio',
    os.path.join(
        'resources',
        'gamma_test.simtel.gz')
)


def test_many_object_reprs():
    # for scripts/print_structure.py the reprs must work
    # therefore this test is here

    with EventIOFile(prod2_path) as file_:
        for obj in yield_all_objects_depth_first(file_):
            assert repr(obj)
