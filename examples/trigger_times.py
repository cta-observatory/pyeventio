# coding: utf-8
from ctapipe.visualization import CameraDisplay
from ctapipe.instrument import CameraGeometry
from eventio import SimTelFile
import astropy.units as u
import numpy as np
import matplotlib.pyplot as plt

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument(
    "inputfile",
    help="Example file: tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz",
)
parser.add_argument("--max-shower-events", type=int, default=0)
parser.add_argument("--interactive", action="store_true")
args = parser.parse_args()

with SimTelFile(args.inputfile) as f:
    # f = SimTelFile('tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz')
    cam = f.telescope_descriptions[1]["camera_settings"]
    geom = CameraGeometry(
        "astri",
        np.arange(cam["n_pixels"]),
        cam["pixel_x"] * u.m,
        cam["pixel_y"] * u.m,
        cam["pixel_area"] * u.m**2,
        pix_type="rectangular",
    )

    it = iter(f)

    plt.ion()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    d1 = CameraDisplay(geom, ax=ax1)
    d2 = CameraDisplay(geom, ax=ax2)

    d1.add_colorbar(ax=ax1)
    d2.add_colorbar(ax=ax2)
    ax1.set_title("ADCSum")
    ax2.set_title("Pixel Trigger Times")

    x = geom.pix_x.to_value(u.m)
    y = geom.pix_y.to_value(u.m)
    for ax in (ax1, ax2):
        ax.set_xlim(1.01 * x.min(), 1.01 * x.max())
        ax.set_ylim(1.01 * y.min(), 1.01 * y.max())

    cmap = plt.get_cmap("viridis")
    cmap.set_bad("gray")
    d2.cmap = cmap

    fig.show()
    fig.tight_layout()

    for i, event in enumerate(f):
        for t in event["telescope_events"].values():
            d1.image = t["adc_samples"][0, :, 0]

            trig = np.full(geom.n_pixels, np.nan)

            trig[t["pixel_timing"]["pixel_list"]] = t["pixel_timing"]["time"][
                t["pixel_timing"]["pixel_list"]
            ][:, 0]  # note: selecting only first type
            trig = np.ma.array(trig, mask=np.isnan(trig))

            d2.image = trig

            if args.interactive:
                input("Enter for next telecope event")
            else:
                fig.savefig(
                    f"simtel_trigger_times_event_{event['event_id']}_tel_{t['header']['telescope_id']}.png"
                )

        if i == args.max_shower_events - 1:
            parser.exit(
                status=0, message="Maximum number of selected shower events reached."
            )
