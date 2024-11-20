import matplotlib.pyplot as plt
import numpy as np

import astropy.units as u

from argparse import ArgumentParser

from ctapipe.instrument import CameraGeometry
from ctapipe.visualization import CameraDisplay

from eventio import EventIOFile
from eventio.simtel import CameraSettings
from eventio.iact import PhotoElectrons, TelescopeData

parser = ArgumentParser()
parser.add_argument(
    "-i",
    "--inputfile",
    dest="inputfile",
    help="Example file: tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz",
)
parser.add_argument("--max-events", default=1)

args = parser.parse_args()


with EventIOFile(args.inputfile) as f:
    cameras = {}
    event_index = 0
    for o in f:
        if event_index == args.max_events:
            break
        if isinstance(o, CameraSettings):
            cam_data = o.parse()
            pix_type = 'square'
            pix_rotation = 0 * u.deg

            cameras[o.telescope_id] = CameraGeometry(
                name="CAM-{}".format(o.telescope_id),
                pix_id=np.arange(cam_data["n_pixels"]),
                pix_x=cam_data["pixel_x"] * u.m,
                pix_y=cam_data["pixel_y"] * u.m,
                pix_area=cam_data["pixel_area"] * u.m**2,
                pix_type=pix_type,
                cam_rotation=cam_data["cam_rot"] * u.rad,
                pix_rotation=pix_rotation,
            )

        if isinstance(o, TelescopeData):
            for subo in o:
                if isinstance(subo, PhotoElectrons):
                    pe = subo.parse()

                    fig = plt.figure()
                    cam = cameras[subo.telescope_id]
                    disp = CameraDisplay(cam)
                    disp.image = pe['photoelectrons']
                    plt.show()
                    plt.close()
            event_index += 1
