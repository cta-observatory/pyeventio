import matplotlib.pyplot as plt
import numpy as np

import astropy.units as u

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from pkg_resources import resource_filename

from eventio import EventIOFile
from eventio.simtel import (
    CameraSettings,
    Event,
    TelescopeEvent,
    ADCSums
)

input_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz'
)

with EventIOFile(input_file) as f:
    cameras = {}
    for o in f:
        if isinstance(o, CameraSettings):
            cam_data = o.parse()

            if cam_data['pixel_shape'][0] == -1:
                pixel_shape = 'hexagonal' if cam_data['n_pixels'] < 2000 else 'square'
            else:
                pixel_shape = 'square' if cam_data['pixel_shape'][0] else 'hexagonal'

            cameras[o.telescope_id] = CameraGeometry(
                cam_id='CAM-{}'.format(o.telescope_id),
                pix_id=np.arange(cam_data['n_pixels']),
                pix_x=cam_data['pixel_x'] *  u.m,
                pix_y=cam_data['pixel_y'] *  u.m,
                pix_area=cam_data['pixel_area'] * u.m**2,
                pix_type=pixel_shape,
                cam_rotation=cam_data['cam_rot'] * u.rad,
            )

        if isinstance(o, Event):
            assert len(cameras) > 0
            for subo in o:
                if isinstance(subo, TelescopeEvent):
                    for subsubo in subo:
                        if isinstance(subsubo, ADCSums):
                            data = subsubo.parse()

                            plt.figure()
                            cam = cameras[subo.telescope_id]
                            disp = CameraDisplay(cam)
                            disp.image = data['adc_sums'][0]
                            plt.show()
