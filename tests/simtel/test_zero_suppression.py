from os import path, environ
import pytest
import numpy as np
from eventio import SimTelFile

TEST_FILE_PATH = path.join(
    environ['TEST_FILE_DIR'],
    (
        'gamma_20deg_180deg_run1187___cta-prod3-demo_desert-2150m-Paranal'
        '-demo2sect_cone10.simtel-clean3.gz'
    )
)


def test_adc_sums():
    pyhessio = pytest.importorskip("pyhessio")
    with pyhessio.open_hessio(TEST_FILE_PATH) as hessio_file:
        eventstream = hessio_file.move_to_next_event()
        for EE, HE in zip(SimTelFile(TEST_FILE_PATH), eventstream):
            EE_tel_ids = sorted(EE['telescope_events'].keys())
            HE_tel_ids = sorted(hessio_file.get_teldata_list())
            assert EE_tel_ids == HE_tel_ids

            for tel_id in HE_tel_ids:
                HE_adc_sum = hessio_file.get_adc_sum(tel_id)
                EE_adc_sum = EE['telescope_events'][tel_id]['adc_sums']
                assert np.array_equal(HE_adc_sum, EE_adc_sum)
