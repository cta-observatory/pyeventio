import numpy as np

simtel_runheader_dtype_v0_or_v1 = np.dtype([
    #(fieldname, type, shape)
    ('shower_prog_id', 'i4'),
    ('shower_prog_vers', 'i4'),
    ('detector_prog_id', 'i4'),
    ('detector_prog_vers', 'i4'),
    ('obsheight', 'f4'),
    ('num_showers', 'i4'),
    ('num_use', 'i4'),
    ('core_pos_mode', 'i4'),
    ('core_range', 'f4', (2,)),
    ('alt_range', 'f4', (2,)),
    ('az_range', 'f4', (2,)),
    ('diffuse', 'i4'),
    ('viewcone', 'f4', (2,)),
    ('E_range', 'f4', ),
    ('spectral_index', 'f4'),
    ('B_total', 'f4'),
    ('B_inclination', 'f4'),
    ('B_declination', 'f4'),
    ('injection_height', 'f4'),
    ('atmosphere', 'i4'),
])

simtel_runheader_dtype_v2 = np.dtype([
    #(fieldname, type, shape)
    ('shower_prog_id', 'i4'),
    ('shower_prog_vers', 'i4'),
    ('detector_prog_id', 'i4'),
    ('detector_prog_vers', 'i4'),
    ('obsheight', 'f4'),
    ('num_showers', 'i4'),
    ('num_use', 'i4'),
    ('core_pos_mode', 'i4'),
    ('core_range', 'f4', (2,)),
    ('alt_range', 'f4', (2,)),
    ('az_range', 'f4', (2,)),
    ('diffuse', 'i4'),
    ('viewcone', 'f4', (2,)),
    ('E_range', 'f4', ),
    ('spectral_index', 'f4'),
    ('B_total', 'f4'),
    ('B_inclination', 'f4'),
    ('B_declination', 'f4'),
    ('injection_height', 'f4'),
    ('atmosphere', 'i4'),
    ('corsika_iact_options', 'i4'),
    ('corsika_low_E_model', 'i4'),
    ('corsika_high_E_model', 'i4'),
    ('corsika_bunchsize', 'f4'),
    ('corsika_wlen_min', 'i4'),
    ('corsika_wlen_max', 'i4'),
])


simtel_runheader_dtype_v3 = np.dtype([
    #(fieldname, type, shape)
    ('shower_prog_id', 'i4'),
    ('shower_prog_vers', 'i4'),
    ('detector_prog_id', 'i4'),
    ('detector_prog_vers', 'i4'),
    ('obsheight', 'f4'),
    ('num_showers', 'i4'),
    ('num_use', 'i4'),
    ('core_pos_mode', 'i4'),
    ('core_range', 'f4', (2,)),
    ('alt_range', 'f4', (2,)),
    ('az_range', 'f4', (2,)),
    ('diffuse', 'i4'),
    ('viewcone', 'f4', (2,)),
    ('E_range', 'f4', ),
    ('spectral_index', 'f4'),
    ('B_total', 'f4'),
    ('B_inclination', 'f4'),
    ('B_declination', 'f4'),
    ('injection_height', 'f4'),
    ('atmosphere', 'i4'),
    ('corsika_iact_options', 'i4'),
    ('corsika_low_E_model', 'i4'),
    ('corsika_high_E_model', 'i4'),
    ('corsika_bunchsize', 'f4'),
    ('corsika_wlen_min', 'i4'),
    ('corsika_wlen_max', 'i4'),
    ('corsika_low_E_detail', 'i4'),
    ('corsika_high_E_detail', 'i4'),
])

simtel_runheader_dtype_v4_or_higher = np.dtype([
    #(fieldname, type, shape)
    ('shower_prog_id', 'i4'),
    ('shower_prog_vers', 'i4'),
    ('shower_prog_start', 'i4'),
    ('detector_prog_id', 'i4'),
    ('detector_prog_vers', 'i4'),
    ('detector_prog_start', 'i4'),
    ('obsheight', 'f4'),
    ('num_showers', 'i4'),
    ('num_use', 'i4'),
    ('core_pos_mode', 'i4'),
    ('core_range', 'f4', (2,)),
    ('alt_range', 'f4', (2,)),
    ('az_range', 'f4', (2,)),
    ('diffuse', 'i4'),
    ('viewcone', 'f4', (2,)),
    ('E_range', 'f4', ),
    ('spectral_index', 'f4'),
    ('B_total', 'f4'),
    ('B_inclination', 'f4'),
    ('B_declination', 'f4'),
    ('injection_height', 'f4'),
    ('atmosphere', 'i4'),
    ('corsika_iact_options', 'i4'),
    ('corsika_low_E_model', 'i4'),
    ('corsika_high_E_model', 'i4'),
    ('corsika_bunchsize', 'f4'),
    ('corsika_wlen_min', 'i4'),
    ('corsika_wlen_max', 'i4'),
    ('corsika_low_E_detail', 'i4'),
    ('corsika_high_E_detail', 'i4'),
])

simtel_runheader_dtype_map = {
    0: simtel_runheader_dtype_v0_or_v1,
    1: simtel_runheader_dtype_v0_or_v1,
    2: simtel_runheader_dtype_v2,
    3: simtel_runheader_dtype_v3,
    4: simtel_runheader_dtype_v4_or_higher,
}
