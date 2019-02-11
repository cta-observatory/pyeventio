from eventio import EventIOFile
from eventio.search_utils import yield_toplevel_of_type


test_file = 'tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'


def test_telescope_ids():
    from eventio.simtel import ArrayEvent, TelescopeEvent

    with EventIOFile(test_file) as f:

        for array_event in yield_toplevel_of_type(f, ArrayEvent):
            for telescope_event in yield_toplevel_of_type(array_event, TelescopeEvent):
                telescope_id = None
                for o in telescope_event:
                    telescope_id = telescope_id or o.telescope_id

                    assert telescope_id == o.telescope_id
