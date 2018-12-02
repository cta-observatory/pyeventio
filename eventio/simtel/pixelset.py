import numpy as np
from functools import lru_cache


dt1 = np.dtype([
    # (fieldname, type, shape)
    ('setup_id', 'i4'),
    ('trigger_mode', 'i4'),
    ('min_pixel_mult', 'i4'),
    ('num_pixels', 'i4'),
])


@lru_cache()
def build_dt2(num_pixels):
    return np.dtype([
        ('pixel_HV_DAC', 'i4', (num_pixels,)),
        ('num_drawers', 'i4'),
    ])


@lru_cache()
def build_dt3(version, num_drawers):
    dt = [
        ('threshold_DAC', 'i4', (num_drawers,)),
        ('num_drawers', 'i4'),
        ('ADC_start', 'i2', (num_drawers,)),
        ('ADC_count', 'i2', (num_drawers,)),
    ]

    if version >= 1:
        dt.extend([
            ('time_slice', 'f4'),
            ('sum_bins', 'i4'),
        ])

    return np.dtype(dt)


# nrefshape = tools.get_scount(data)
# lrefshape = tools.get_scount(data)
def build_dt4(nrefshape, lrefshape):
    return np.dtype([
        ('ref_step', 'f4'),
        ('refshape', 'f2', (nrefshape, lrefshape)),
    ])
