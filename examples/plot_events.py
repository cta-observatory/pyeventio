import matplotlib.pyplot as plt
import numpy as np
from pkg_resources import resource_filename

import astropy.units as u

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from eventio import EventIOFile
from eventio.simtel import (
    SimTelCamSettings,
    SimTelEvent,
    SimTelTelEvent,
    SimTelTelADCSamp
)

input_file = resource_filename(
    'eventio',
    'resources/gamma_test.simtel.gz'
)


with EventIOFile(input_file) as f:
    cameras = {}
    for o in f:
        if isinstance(o, SimTelCamSettings):
            cam_data = o.parse_data_field()

            if cam_data['pixel_shape'][0] == -1:
                pixel_shape = 'hexagonal' if cam_data['n_pixels'] < 2000 else 'square'
            else:
                pixel_shape = 'hexagonal' if cam_data['pixel_shape'][0] else 'square'

            cameras[o.telescope_id] = CameraGeometry(
                cam_id='CAM-{}'.format(o.telescope_id),
                pix_id=np.arange(cam_data['n_pixels']),
                pix_x=cam_data['pixel_x'] *  u.m,
                pix_y=cam_data['pixel_y'] *  u.m,
                pix_area=cam_data['pixel_area'] * u.m**2,
                pix_type=pixel_shape,
                cam_rotation=cam_data['cam_rot'] * u.rad,
            )

        if isinstance(o, SimTelEvent):
            for subo in o:
                if isinstance(subo, SimTelTelEvent):
                    for subsubo in subo:
                        if isinstance(subsubo, SimTelTelADCSamp):
                            data = subsubo.parse_data_field()

                            gain, pix, chan = np.where(data == data.max())

                            plt.figure()
                            cam = cameras[subo.telescope_id]
                            disp = CameraDisplay(cam)
                            disp.image = data[gain[0]].sum(axis=1)
                            plt.show()
