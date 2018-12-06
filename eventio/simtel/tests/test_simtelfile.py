import pkg_resources
import os

from eventio.simtel import SimTelFile

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


def test_show_we_get_a_dict_with_hower_and_event():
    for path in test_paths:
        for event in SimTelFile(path):
            assert 'mc_shower' in event
            assert 'array_event' in event
            assert 'mc_event' in event
            break


def test_show_event_is_not_empty_and_has_some_members_for_sure():
    for path in test_paths:
        for event in SimTelFile(path):
            assert event['mc_shower'].keys() == {
                'shower',
                'primary_id',
                'energy',
                'azimuth',
                'altitude',
                'depth_start',
                'h_first_int',
                'xmax',
                'hmax',
                'emax',
                'cmax',
                'n_profiles',
                'profiles'
            }

            print(event.keys())
            assert event.keys() == {
                'mc_shower',
                'mc_event',
                'array_event',
                'photoelectron_sums',
                'photoelectrons',
                'camera_monitorings',
                'laser_calibrations',
            }

            array_event = event['array_event']
            assert array_event.keys() == {
                'trigger_information', 'telescope_events', 'tracking_positions'
            }

            telescope_events = array_event['telescope_events']

            assert telescope_events  # never empty!

            for telescope_event in telescope_events.values():
                expected_keys = {
                    'header',
                    'pixel_timing',
                }
                allowed_keys = {
                    'image_parameters',
                    'pixel_list',
                    'adc_sums',
                    'adc_samples'
                }

                found_keys = set(telescope_event.keys())
                assert expected_keys.issubset(found_keys)

                extra_keys = found_keys.difference(expected_keys)
                assert extra_keys.issubset(allowed_keys)
                assert 'adc_sums' in found_keys or 'adc_samples' in found_keys

            break


def test_iterate_complete_file():
    expected_counter_values = {
        prod2_path: 8,
        prod3_path: 5,
        prod4_path: 30,
        prod4_zst_path: 30,  # the same of course
    }
    for path in test_paths:
        try:
            for counter, event in enumerate(SimTelFile(path)):
                pass
        except (EOFError, IndexError):  # truncated files might raise these...
            pass
        assert counter == expected_counter_values[path]
