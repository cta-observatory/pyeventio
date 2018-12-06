import matplotlib.pyplot as plt
import numpy as np
from pkg_resources import resource_filename

import astropy.units as u

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from eventio import EventIOFile
from eventio.simtel import (
    CameraSettings,
    Event,
    TelescopeEvent,
    ADCSamples
)

input_file = resource_filename(
    'eventio',
    'gamma_test.simtel.gz',
)
input_file = '/home/maxnoe/Downloads/gamma_20deg_180deg_run7360___cta-prod3-merged_desert-2150m-Paranal-3HB89-NGFD.simtel.gz'


with EventIOFile(input_file) as f:
    cameras = {}
    for o in f:
        if isinstance(o, CameraSettings):
            cam_data = o.parse_data_field()

            if cam_data['pixel_shape'][0] == 2:
                pix_type = 'square'
                pix_rotation = 0 * u.deg

            elif cam_data['pixel_shape'][0] == 1:
                pix_type = 'hexagonal'

                if cam_data['n_pixels'] == 1855:
                    pix_rotation = 0 * u.deg
                else:
                    pix_rotation = 30 * u.deg

            elif cam_data['pixel_shape'][0] == -1:
                if cam_data['n_pixels'] > 2000:
                    pix_type = 'square'
                    pix_rotation = 0 * u.deg
                else:
                    pix_type = 'hexagonal'
                    pix_rotation = 0 * u.deg

            cameras[o.telescope_id] = CameraGeometry(
                cam_id='CAM-{}'.format(o.telescope_id),
                pix_id=np.arange(cam_data['n_pixels']),
                pix_x=cam_data['pixel_x'] * u.m,
                pix_y=cam_data['pixel_y'] * u.m,
                pix_area=cam_data['pixel_area'] * u.m**2,
                pix_type=pix_type,
                cam_rotation=cam_data['cam_rot'] * u.rad,
                pix_rotation=pix_rotation,
            )

        if isinstance(o, Event):
            for subo in o:
                if isinstance(subo, TelescopeEvent):
                    for subsubo in subo:
                        if isinstance(subsubo, ADCSamples):
                            data = subsubo.parse_data_field()

                            gain, pix, chan = np.where(data == data.max())

                            plt.figure()
                            cam = cameras[subo.telescope_id]
                            disp = CameraDisplay(cam)
                            disp.image = data[gain[0]].sum(axis=1)
                            plt.show()
