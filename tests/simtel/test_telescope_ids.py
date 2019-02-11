from eventio import EventIOFile
from eventio.search_utils import yield_toplevel_of_type


test_files = [
    'tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz',
    'tests/resources/gamma_test.simtel.gz',
]


def test_telescope_ids():
    from eventio.simtel import ArrayEvent, TelescopeEvent

    def assert_event_has_equal_telids(event):
        for telescope in yield_toplevel_of_type(event, TelescopeEvent):
            for o in telescope:
                assert o.telescope_id == telescope.telescope_id

    for test_file in test_files:
        try:
            with EventIOFile(test_file) as f:
                for event in yield_toplevel_of_type(f, ArrayEvent):
                    assert_event_has_equal_telids(event)
        except EOFError:
            pass
