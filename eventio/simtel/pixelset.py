import numpy as np
from functools import lru_cache


dt1 = np.dtype([
    # (fieldname, type, shape)
    ('setup_id', 'i4'),
    ('trigger_mode', 'i4'),
    ('min_pixel_mult', 'i4'),
    ('n_pixels', 'i4'),
])


@lru_cache()
def build_dt2(n_pixels):
    return np.dtype([
        ('pixel_HV_DAC', 'i4', (n_pixels,)),
        ('n_drawers', 'i4'),
    ])


@lru_cache()
def build_dt3(version, n_drawers):
    dt = [
        ('threshold_DAC', 'i4', (n_drawers,)),
        ('n_drawers', 'i4'),
        ('ADC_start', 'i2', (n_drawers,)),
        ('ADC_count', 'i2', (n_drawers,)),
    ]

    if version >= 1:
        dt.extend([
            ('time_slice', 'f4'),
            ('sum_bins', 'i4'),
        ])

    return np.dtype(dt)


# nref_shape = tools.get_scount(data)
# lref_shape = tools.get_scount(data)
def build_dt4(n_ref_shape, l_ref_shape):
    return np.dtype([
        ('ref_step', 'f4'),
        ('ref_shape', 'f2', (n_ref_shape, l_ref_shape)),
    ])
