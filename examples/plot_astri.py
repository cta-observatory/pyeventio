import matplotlib.pyplot as plt
import numpy as np

import astropy.units as u

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from pkg_resources import resource_filename

from eventio.simtel import SimTelFile
from functools import lru_cache

input_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'
)


@lru_cache()
def build_cam_geom(f, telescope_id):
    cam_data = f.telescope_descriptions[telescope_id]['camera_settings']
    return CameraGeometry(
        cam_id='CAM-{}'.format(telescope_id),
        pix_id=np.arange(cam_data['n_pixels']),
        pix_x=cam_data['pixel_x'] * u.m,
        pix_y=cam_data['pixel_y'] * u.m,
        pix_area=cam_data['pixel_area'] * u.m**2,
        pix_type='square',
        cam_rotation=cam_data['cam_rot'] * u.rad,
    )


with SimTelFile(input_file) as f:
    for array_event in f:
        print('Event:', array_event['event_id'])
        for telescope_id, event in array_event['telescope_events'].items():
            print('Telescope:', telescope_id)

            cam = build_cam_geom(f, telescope_id)

            plt.figure()
            disp = CameraDisplay(cam)
            disp.image = event['adc_sums'][0]
            plt.show()
