import pkg_resources
from os import path

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'gamma_test.simtel.gz')
)


def test_2002():
    from eventio import EventIOFile
    from eventio.simtel.objects import SimTelCamSettings

    with EventIOFile(testfile) as f:
        obj = next(f)
        while obj.header.type != SimTelCamSettings.eventio_type:
            obj = next(f)

        # first camera should be the LST
        camera_data = obj.parse_data_field()
        assert camera_data['telescope_id'] == 1
        assert camera_data['n_pixels'] == 1855
        assert camera_data['focal_length'] == 28.0
        assert len(camera_data['pixel_x']) == 1855
        assert len(camera_data['pixel_y']) == 1855
