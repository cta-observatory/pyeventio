from os import path, environ
import pytest
import numpy as np
from eventio import SimTelFile

TEST_FILE_PATH = path.join(
    environ.get('TEST_FILE_DIR', ''), 'test.simtel-clean3.gz'
)

TEST_FILE_PATH_NORMAL = path.join(
    environ.get('TEST_FILE_DIR', ''), 'test.simtel_10MB_part.gz'
)


def is_testfile_missing():
    return (
        not path.exists(TEST_FILE_PATH)
        or not path.exists(TEST_FILE_PATH_NORMAL)
    )


@pytest.mark.skipif(is_testfile_missing(), reason="testfile_missing")
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


@pytest.mark.skipif(is_testfile_missing(), reason="testfile_missing")
def test_adc_samples():
    seen_at_least_one_event = False
    # testing on 10MB_part, so expecting EOF Error here
    with pytest.raises(EOFError):
        for z, e in zip(
            SimTelFile(TEST_FILE_PATH),
            SimTelFile(TEST_FILE_PATH_NORMAL)
        ):
            for tel_id in e['telescope_events']:
                try:
                    zas = z['telescope_events'][tel_id]['adc_samples']
                    eas = e['telescope_events'][tel_id]['adc_samples']
                    survivors = (zas != 0).all(axis=-1)
                    assert survivors.sum() > 0
                    assert np.array_equal(zas[survivors], eas[survivors])
                    seen_at_least_one_event = True
                except KeyError as exc:
                    print(
                        'event:', e['event_id'],
                        'tel:', tel_id,
                        'KeyError:', exc
                    )

    assert seen_at_least_one_event
