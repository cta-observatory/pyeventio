import numpy as np
from functools import lru_cache


@lru_cache(maxsize=1)
def build_dtype_part1(version):
    #  (fieldname, type, shape)
    dtype = [
        ('run', 'i4'),
        ('time', 'i4'),
        ('run_type', 'i4'),
        ('tracking_mode', 'i4'),
    ]

    if version >= 2:
        dtype.append(('reverse_flag', 'i4'))

    dtype.extend([
        ('direction', 'f4', (2,)),
        ('offset_fov', 'f4', (2,)),
        ('conv_depth', 'f4'),
    ])
    if version >= 1:
        dtype.append(('conv_ref_pos', 'f4', (2,)))

    dtype.append(('n_telescopes', 'i4'))

    return np.dtype(dtype)


@lru_cache()
def build_dtype_part2(version, n_telescopes):
    return np.dtype([
        #  (fieldname, type, shape)
        ('tel_id', 'i2', (n_telescopes,)),
        ('tel_pos', 'f4', (n_telescopes, 3)),
        ('min_tel_trig', 'i4'),
        ('duration', 'i4', ),
    ])
