# coding: utf-8
from ctapipe.visualization import CameraDisplay
from ctapipe.instrument import CameraGeometry
from eventio import SimTelFile
import astropy.units as u
import numpy as np
import matplotlib.pyplot as plt



f = SimTelFile('tests/resources/gamma_20deg_0deg_run103___cta-prod4-sst-astri_desert-2150m-Paranal-sst-astri.simtel.gz')
cam = f.telescope_descriptions[1]['camera_settings']
geom = CameraGeometry(
    'astri',
    np.arange(cam['n_pixels']),
    cam['pixel_x'] * u.m,
    cam['pixel_y'] * u.m,
    cam['pixel_area']* u.m**2,
    pix_type='rectangular',
)


it = iter(f)

plt.ion()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

d1 = CameraDisplay(geom, ax=ax1)
d2 = CameraDisplay(geom, ax=ax2)

d1.add_colorbar(ax=ax1)
d2.add_colorbar(ax=ax2)
ax1.set_title('ADCSum')
ax2.set_title('Pixel Trigger Times')

x = geom.pix_x.to_value(u.m)
y = geom.pix_y.to_value(u.m)
for ax in (ax1, ax2):
    ax.set_xlim(1.01 * x.min(), 1.01 * x.max())
    ax.set_ylim(1.01 * y.min(), 1.01 * y.max())

cmap = plt.get_cmap('viridis')
cmap.set_bad('gray')
d2.cmap = cmap

fig.show()
fig.tight_layout()


for event in f:
    for t in event['telescope_events'].values():

        d1.image = t['adc_sums'][0]

        trig = np.full(geom.n_pixels, np.nan)
        trig[t['pixel_trigger_times']['pixel_ids']] = t['pixel_trigger_times']['trigger_times']
        trig = np.ma.array(trig, mask=np.isnan(trig))

        d2.image = trig

        input('Enter for next telecope event')
