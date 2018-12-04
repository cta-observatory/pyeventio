import pytest
from pkg_resources import resource_filename
import numpy as np
pyhessio = pytest.importorskip("pyhessio")

testfile = resource_filename('eventio', 'resources/gamma_test_large_truncated.simtel.gz')


def test_adc_samples():
    from eventio import EventIOFile
    from eventio.simtel import (
        SimTelEvent, SimTelTelEvent, SimTelTelADCSamp, SimTelMCEvent
    )
    from eventio.search_utils import yield_toplevel_of_type

    events_compared = 0
    current_event = -1
    with pyhessio.open_hessio(testfile) as h, EventIOFile(testfile) as e:
        hessio_events = h.move_to_next_event()

        try:

            for o in e:
                if isinstance(o, SimTelMCEvent):
                    current_event = o.header.id

                if isinstance(o, SimTelEvent):
                    hessio_event = next(hessio_events)

                    for televent in yield_toplevel_of_type(o, SimTelTelEvent):
                        for adcsamp in yield_toplevel_of_type(televent, SimTelTelADCSamp):
                            assert hessio_event == current_event
                            tel_id = adcsamp.telescope_id
                            assert tel_id in h.get_teldata_list()

                            adcsamp_eventio = adcsamp.parse_data_field()
                            adcsamp_hessio = h.get_adc_sample(tel_id)

                            assert np.all(adcsamp_eventio == adcsamp_hessio)
                            events_compared += 1

                            if events_compared >= 10:
                                raise StopIteration

        except StopIteration:
            pass

        assert events_compared == 10
