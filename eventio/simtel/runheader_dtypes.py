import numpy as np

runheader_dtype_part1 = np.dtype([
    #(fieldname, type, shape)
    ('run', 'i4'),
    ('time', 'i4'),
    ('run_type', 'i4'),
    ('tracking_mode', 'i4'),
    ('reverse_flag', 'i4'),
    ('direction', 'f4', (2,)),
    ('offset_fov', 'f4', (2,)),
    ('conv_depth', 'f4'),
    ('conv_ref_pos', 'f4', (2,)),
    ('ntel', 'i4'),
])

def runheader_dtype_part2(ntel):
    return np.dtype([
        #(fieldname, type, shape)
        ('tel_id', 'i2', (ntel,)),
        ('tel_pos', 'f4', (ntel, 3)),
        ('min_tel_trig', 'i4'),
        ('duration', 'i4', ),
        ('spectral_index', 'f4'),
        ('B_total', 'f4'),
        ('B_inclination', 'f4'),
        ('B_declination', 'f4'),
        ('injection_height', 'f4'),
        ('atmosphere', 'i4'),
    ])

