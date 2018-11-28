import numpy as np

runheader_dtype_part1 = np.dtype([
    #  (fieldname, type, shape)
    ('run', 'i4'),
    ('time', 'i4'),
    ('run_type', 'i4'),
    ('tracking_mode', 'i4'),
    ('reverse_flag', 'i4'),
    ('direction', 'f4', (2,)),
    ('offset_fov', 'f4', (2,)),
    ('conv_depth', 'f4'),
    ('conv_ref_pos', 'f4', (2,)),
    ('n_telescopes', 'i4'),
])


def runheader_dtype_part2(n_telescopes):
    return np.dtype([
        #  (fieldname, type, shape)
        ('tel_id', 'i2', (n_telescopes,)),
        ('tel_pos', 'f4', (n_telescopes, 3)),
        ('min_tel_trig', 'i4'),
        ('duration', 'i4', ),
    ])
