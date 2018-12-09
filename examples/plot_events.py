import matplotlib.pyplot as plt
import numpy as np
from argparse import ArgumentParser
from functools import lru_cache

import astropy.units as u

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from eventio.simtel import SimTelFile


parser = ArgumentParser()
parser.add_argument('inputfile')
args = parser.parse_args()


@lru_cache()
def build_cam_geom(simtel_file, telescope_id):
    cam_data = simtel_file.telescope_descriptions[telescope_id]['camera_settings']

    if cam_data['pixel_shape'][0] == 2:
        pix_type = 'square'
        pix_rotation = 0 * u.deg

    elif cam_data['pixel_shape'][0] == 1:
        pix_type = 'hexagonal'

        # LST has 0 deg rotation, MST 30 (flat top vs. pointy top hexagons)
        if cam_data['n_pixels'] == 1855:
            pix_rotation = 0 * u.deg
        else:
            pix_rotation = 30 * u.deg

    # if pix_type == -1, we have to guess
    elif cam_data['pixel_shape'][0] == -1:
        if cam_data['n_pixels'] > 2000:
            pix_type = 'square'
            pix_rotation = 0 * u.deg
        else:
            pix_type = 'hexagonal'

            # LST has 0 deg rotation, MST 30 (flat top vs. pointy top hexagons)
            if cam_data['n_pixels'] == 1855:
                pix_rotation = 0 * u.deg
            else:
                pix_rotation = 30 * u.deg

    return CameraGeometry(
        cam_id='CAM-{}'.format(telescope_id),
        pix_id=np.arange(cam_data['n_pixels']),
        pix_x=cam_data['pixel_x'] * u.m,
        pix_y=cam_data['pixel_y'] * u.m,
        pix_area=cam_data['pixel_area'] * u.m**2,
        pix_type=pix_type,
        cam_rotation=cam_data['cam_rot'] * u.rad,
        pix_rotation=pix_rotation,
    )


with SimTelFile(args.inputfile) as f:
    for array_event in f:
        print('Event:', array_event['event_id'])
        for telescope_id, event in array_event['telescope_events'].items():
            print('Telescope:', telescope_id)

            data = event.get('adc_samples')
            if data is None:
                data = event['adc_sums'][:, :, np.newaxis]

            image = data[0].sum(axis=1)

            cam = build_cam_geom(f, telescope_id)

            plt.figure()
            disp = CameraDisplay(cam)
            disp.image = image
            plt.show()
