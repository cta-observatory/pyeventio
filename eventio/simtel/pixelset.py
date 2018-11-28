import numpy as np

__version__ = 2

dt1 = np.dtype([
    #(fieldname, type, shape)
    ('setup_id', 'i4'),
    ('trigger_mode', 'i4'),
    ('min_pixel_mult', 'i4'),
    ('num_pixels', 'i4'),
])

def dt2(num_pixels):
    return np.dtype([
        ('pixel_HV_DAC', 'i4', (num_pixels,)),
        ('num_drawers', 'i4'),
    ])

def dt3(num_drawers):
    return np.dtype([
        ('threshold_DAC', 'i4', (num_drawers,)),
        ('num_drawers_again', 'i4'),
        ('ADC_start', 'i2', (num_drawers,)),
        ('ADC_count', 'i2', (num_drawers,)),
        ('time_slice', 'f4'),  # not in V<1
        ('sum_bins', 'i4'),    # not in V<1
    ])


# nrefshape = tools.get_scount(data)
# lrefshape = tools.get_scount(data)
def dt4(nrefshape, lrefshape):
    return np.dtype([
        ('ref_step', 'f4'),
        ('refshape', 'f2', (nrefshape, lrefshape)),
    ])
