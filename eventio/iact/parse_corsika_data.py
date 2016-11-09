import numpy as np
from functools import namedtuple
from datetime import date


def float_to_date(date_float, base_year=2000):
    '''
    Convert a float of the form YYMMDD.0 to a datetime.date
    '''
    assert float(date_float).is_integer()
    year = int(round(date_float)) // 10000 + base_year
    month = int(round(date_float % 10000)) // 100
    day = int(round(date_float % 100))

    return date(year=year, month=month, day=day)


CorsikaRunHeader = namedtuple('CorsikaRunHeader', [
    'run_id',
    'date_of_begin_run',
    'corsika_version',
    'observation_levels',
    'energy_slope',
    'energy_range',
    'EGS4_flag',
    'NKG_flag',
    'hadron_cutoff_energy',
    'muon_cutoff_energy',
    'electron_cutoff_energy',
    'photon_cutoff_energy',
    'phyiscal_constants',
    'inclinded_observation_plane_x',
    'inclinded_observation_plane_y',
    'inclinded_observation_plane_z',
    'inclinded_observation_plane_theta',
    'inclinded_observation_plane_phi',
    'NSHOW',
    'CKA',
    'CETA',
    'CSTRBA',
    'scatter_range_x',
    'scatter_range_y',
    'HLAY',
    'AATM',
    'BATM',
    'CATM',
    'NFLAIN',
    'NFLDIF',
    'NFLPI0_plus_100_times_NFLPIF',
    'NFLCHE_plus_100_times_NFRAGM',
])


def parse_corsika_run_header(run_header):
    h = run_header
    n_obs_levels = int(round(h[4]))
    if (n_obs_levels < 1) or (n_obs_levels > 10):
        raise ValueError(
            'number of observation levels n must be 0 < n < 11, but is: {}'.format(h[4])
        )

    return CorsikaRunHeader(
        run_id=h[1],
        date_of_begin_run=float_to_date(h[2]),
        corsika_version=h[3],
        observation_levels=h[5:5+n_obs_levels],
        energy_slope=h[15],
        energy_range=h[16:18],
        EGS4_flag=h[18],
        NKG_flag=h[19],
        hadron_cutoff_energy=h[20],
        muon_cutoff_energy=h[21],
        electron_cutoff_energy=h[22],
        photon_cutoff_energy=h[23],
        phyiscal_constants=h[24:74],
        inclinded_observation_plane_x=h[74],
        inclinded_observation_plane_y=h[75],
        inclinded_observation_plane_z=h[76],
        inclinded_observation_plane_theta=h[77],
        inclinded_observation_plane_phi=h[78],
        NSHOW=h[93],
        CKA=h[94:134],
        CETA=h[134:139],
        CSTRBA=h[139:150],
        scatter_range_x=h[247],
        scatter_range_y=h[248],
        HLAY=h[249:254],
        AATM=h[254:259],
        BATM=h[259:264],
        CATM=h[264:269],
        NFLAIN=h[269],
        NFLDIF=h[270],
        NFLPI0_plus_100_times_NFLPIF=h[271],
        NFLCHE_plus_100_times_NFRAGM=h[272],
    )


CorsikaEventHeader = namedtuple('CorsikaEventHeader', [
    'event_id',
    'particle_id',
    'total_energy',
    'starting_altitude',
    'number_of_first_target_if_fixed',
    'first_interaction_height',
    'momentum_x',
    'momentum_y',
    'momentum_z',
    'zenith_angle',
    'azimuth_angle',
    'seed_info',
    'run_id',
    'date_of_begin_run',
    'corsika_version',
    'observation_levels',
    'energy_slope',
    'energy_range',
    'hadron_cutoff_energy',
    'muon_cutoff_energy',
    'electron_cutoff_energy',
    'photon_cutoff_energy',
    'NFLAIN',
    'NFLDIF',
    'NFLPI0',
    'NFLPIF',
    'NFLCHE',
    'NFRAGM',
    'magnetic_field_x_component',
    'magnetic_field_z_component',
    'EGS4_flag',
    'NKG_flag',
    'low_energy_hadr_model_flag',
    'high_energy_hadr_model_flag',
    'cherenkov_bitmap',
    'neutrino_flag',
    'curved_flag',
    'unix_or_mac_flag',
    'lower_theta_limit',
    'upper_theta_limit',
    'lower_phi_limit',
    'upper_phi_limit',
    'cherenkov_bunch_size',
    'number_of_cherenkov_detectors_in_x_direction',
    'number_of_cherenkov_detectors_in_y_direction',
    'spacing_of_cherenkov_detectors_in_x_direction',
    'spacing_of_cherenkov_detectors_in_y_direction',
    'length_of_each_cherenkov_detector_in_x_direction',
    'length_of_each_cherenkov_detector_in_y_direction',
    'cherenkov_output_to_dedicated_cherenkov_output_file',
    'angle_between_x_direction_and_magnetic_north',
    'additional_muon_output_flag',
    'EGS4_multiple_scattering_step_length_factor',
    'cherenkov_bandwidth_lower_end',
    'cherenkov_bandwidth_upper_end',
    'n_reuse',
    'core_location',
    'sibyll',
    'qgsjet',
    'dpmjet',
    'venus_cross_section_flag',
    'muon_multiple_scattering_flag',
    'nkg_radial_distribution_range',
    'efrcthn',
    'weight_limit_for_thinning_hadronic',
    'weight_limit_for_thinning_em_particles',
    'max_radius_for_radial_thinning',
    'viewcone_inner_angle',
    'viewcone_outer_angle',
    'transition_energy_high_low_energy_model',
    'skimming_incidence_flag',
    'altitude_of_horizontal_shower_axis',
    'starting_height',
    'charm_generation_flag',
    'hadron_origin_of_em_subshower_flag',
    'observation_level_curvature_flag',
])


def parse_corsika_event_header(event_header):
    h = event_header

    n_random_number_sequences = int(round(h[12]))
    if (n_random_number_sequences < 1) or (n_random_number_sequences > 10):
        raise ValueError(
            'Number of random seed sequences must be 0 < n < 11, but is: {}'.format(h[12])
        )
    seed_info = h[13:13 + 3 * n_random_number_sequences].reshape(
        n_random_number_sequences, 3
    )

    n_obs_levels = int(round(h[46]))
    if (n_obs_levels < 1) or (n_obs_levels > 10):
        raise ValueError(
            'number of observation levels n must be 0 < n < 11, but is: {}'.format(h[4])
        )

    n_reuse = int(h[97])
    core_x = h[98:98+n_reuse],
    core_y = h[118:118+n_reuse],

    return CorsikaEventHeader(
        event_id=int(round(h[1])),
        particle_id=int(round(h[2])),
        total_energy=h[3],
        starting_altitude=h[4],
        number_of_first_target_if_fixed=h[5],
        first_interaction_height=h[6],
        momentum_x=h[7],
        momentum_y=h[8],
        momentum_z=h[9],
        zenith_angle=h[10],
        azimuth_angle=h[11],
        seed_info=seed_info,
        run_id=int(round(h[43])),
        date_of_begin_run=float_to_date(h[44]),
        corsika_version=h[45],
        observation_levels=h[47:47 + n_obs_levels],
        energy_slope=h[57],
        energy_range=h[58:60],
        hadron_cutoff_energy=h[60],
        muon_cutoff_energy=h[61],
        electron_cutoff_energy=h[62],
        photon_cutoff_energy=h[63],
        NFLAIN=h[64],
        NFLDIF=h[65],
        NFLPI0=h[66],
        NFLPIF=h[67],
        NFLCHE=h[68],
        NFRAGM=h[69],
        magnetic_field_x_component=h[70],
        magnetic_field_z_component=h[71],
        EGS4_flag=h[72],
        NKG_flag=h[73],
        low_energy_hadr_model_flag=h[74],
        high_energy_hadr_model_flag=h[75],
        cherenkov_bitmap=hex(int(round(h[76]))),
        neutrino_flag=h[77],
        curved_flag=h[78],
        unix_or_mac_flag=h[79],
        lower_theta_limit=h[80],
        upper_theta_limit=h[81],
        lower_phi_limit=h[82],
        upper_phi_limit=h[83],
        cherenkov_bunch_size=h[84],
        number_of_cherenkov_detectors_in_x_direction=h[85],
        number_of_cherenkov_detectors_in_y_direction=h[86],
        spacing_of_cherenkov_detectors_in_x_direction=h[87],
        spacing_of_cherenkov_detectors_in_y_direction=h[88],
        length_of_each_cherenkov_detector_in_x_direction=h[89],
        length_of_each_cherenkov_detector_in_y_direction=h[90],
        cherenkov_output_to_dedicated_cherenkov_output_file=h[91],
        angle_between_x_direction_and_magnetic_north=h[92],
        additional_muon_output_flag=h[93],
        EGS4_multiple_scattering_step_length_factor=h[94],
        cherenkov_bandwidth_lower_end=h[95],
        cherenkov_bandwidth_upper_end=h[96],
        n_reuse=n_reuse,
        core_location=np.vstack((core_x, core_y)).transpose(),
        sibyll={'interaction_flag': h[138], 'cross_section_flag': h[139]},
        qgsjet={'interaction_flag': h[140], 'cross_section_flag': h[141]},
        dpmjet={'interaction_flag': h[142], 'cross_section_flag': h[143]},
        venus_cross_section_flag=h[144],
        muon_multiple_scattering_flag=h[145],
        nkg_radial_distribution_range=h[146],
        efrcthn={
            'energy fraction of thinning level hadronic': h[147],
            'energy fraction of thinning level em-particles': h[148]
        },
        weight_limit_for_thinning_hadronic=h[149],
        weight_limit_for_thinning_em_particles=h[150],
        max_radius_for_radial_thinning=h[151],
        viewcone_inner_angle=h[152],
        viewcone_outer_angle=h[152],
        transition_energy_high_low_energy_model=h[154],
        skimming_incidence_flag=h[155],
        altitude_of_horizontal_shower_axis=h[156],
        starting_height=h[157],
        charm_generation_flag=h[158],
        hadron_origin_of_em_subshower_flag=h[159],
        observation_level_curvature_flag=h[167],
    )
