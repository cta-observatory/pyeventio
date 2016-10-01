''' Methods to read in and parse the IACT EventIO object types '''
import numpy as np

from .tools import unpack_from, read_ints

__all__ = [
    'iact_types',
    'read_type_1200',
    'read_type_1201',
    'read_type_1202',
    'read_type_1203',
    'read_type_1212',
    'read_type_1209',
    'read_type_1210',
    'read_type_1204',
    'parse_corsika_run_header',
    'parse_corsika_event_header',
]


def read_type_1200(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise ValueError('Wrong size: was not 273 but {}'.format(n))

    block = np.frombuffer(
        f.read(n * 4),
        dtype=np.float32,
        count=n
    )

    return parse_corsika_run_header(block)


def read_type_1201(f, head=None):
    ''' ---> write_tel_pos
    int32 ntel
    float32 x[ntel]
    float32 y[ntel]
    float32 z[ntel]
    float32 r[ntel]
    '''
    ntel, = unpack_from('i', f)
    number_of_following_arrays = int((head.length - 4) / ntel / 4)
    if number_of_following_arrays != 4:
        # DN: I think this cannot happen, but who knows.
        msg = 'Number_of_following_arrays is: {}'
        raise Exception(msg.format(number_of_following_arrays))

    tel_pos = np.empty(
        ntel,
        dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('r', 'f4')],
    )

    arrays = np.frombuffer(
        f.read(ntel * 4 * 4),
        dtype=np.float32,
        count=ntel * 4
    )
    arrays = arrays.reshape(4, ntel)
    x, y, z, r = np.vsplit(arrays, 4)

    tel_pos['x'] = x
    tel_pos['y'] = y
    tel_pos['z'] = z
    tel_pos['r'] = r

    return tel_pos


def read_type_1202(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise Exception('read_type_1200: first n was not 273 but '+str(n))

    block = np.frombuffer(
        f.read(n*4),
        dtype=np.float32,
        count=n)

    return parse_corsika_event_header(block)


def read_type_1203(f, head=None):
    ''' ---> write_tel_offset

    int32 narray,
    float32 toff,
    float32 xoff[narray]
    float32 yoff[narray]
    maybe:
        float32 weight[narray]

    '''
    length_first_two = 4 + 4
    narray, toff = unpack_from('if', f)
    number_of_following_arrays = int((head.length - length_first_two) / narray / 4)
    if number_of_following_arrays not in [2, 3]:
        # dneise: I think this cannot happen, but who knows.
        msg = 'in read_type_1201: number_of_following_arrays is: {}'
        raise Exception(msg.format(number_of_following_arrays))

    xoff = np.frombuffer(
        f.read(narray * 4),
        dtype=np.float32,
        count=narray,
    )
    yoff = np.frombuffer(
        f.read(narray * 4),
        dtype=np.float32,
        count=narray,
    )
    weight = np.ones(narray, dtype=np.float32)

    if number_of_following_arrays == 3:
        weight = np.frombuffer(f.read(narray * 4), dtype=np.float32, count=narray)

    return narray, toff, xoff, yoff, weight


def read_type_1204(f, head=None, headers_only=True):
    if not head.only_sub_objects:
        raise Exception('Type 1204 ususally has only sub objects, this one has not!!')
    return list(pb.photon_bunches(f, headers_only=headers_only))


def read_type_1209(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise Exception('read_type_1209: first n was not 273 but '+str(n))

    block = np.frombuffer(
        f.read(n*4),
        dtype=np.float32,
        count=n)

    return block


def read_type_1210(f, head=None):
    n, = read_ints(1, f)
    block = np.frombuffer(
        f.read(n*4),
        dtype=np.float32,
        count=n)
    return block


def read_type_1212(f, head=None):
    return f.read(head.length)


def parse_corsika_event_header(event_header):
    ''' parse the event header of a corsika file into a dict

    **this function is called by parseByteStringToDict()** and a user normally
    does not need to call this function directly.

    The event header of a corsika file is a 272 float list,
    where each number has a meaning by its position in the list.
    This is documented in the Corsika Manual.
    this is just moving the plain 272-float numbers from the original
    header int a dict.
    Not sure, if the key naming is well done :-/
    '''
    h = event_header
    d = dict()
    d['event number'] = int(round(h[1]))
    d['particle id (particle code or A x 100 + Z for nuclei)'] = int(round(h[2]))
    d['total energy in GeV'] = h[3]
    d['starting altitude in g/cm2'] = h[4]
    d['number of first target if fixed'] = h[5]
    d['z coordinate (height) of first interaction in cm'] = h[6]
    d['momentum in GeV/c in (x, y, -z) direction;'] = h[7:10]
    d['angle in radian: (zenith, azimuth)'] = h[10:12]
    n_random_number_sequences = int(round(h[12]))
    if (n_random_number_sequences < 1) or (n_random_number_sequences > 10):
        ValueException('number of random number sequences n must be 0 < n < 11, but is: '+str(h[12]))
    seed_info = h[13:13 + 3*n_random_number_sequences].reshape(n_random_number_sequences,-1)
    d['random number sequences: (seed, #calls, #billion calls)']=seed_info
    d['run number'] = h[43]
    d['date of begin run (yymmdd)'] = int(round(h[44]))
    d['version of program'] = h[45]
    n_obs_levels = int(round(h[46]))
    if (n_obs_levels < 1) or (n_obs_levels > 10):
        ValueException('number of observation levels n must be 0 < n < 11, but is: '+str(h[46]))
    d['observation levels']=h[47:47+n_obs_levels].reshape(n_obs_levels,-1)
    d['slope of energy spektrum']=h[57]
    d['energy range']=h[58:60]
    d['kin. energy cutoff for hadrons in GeV'] = h[60]
    d['kin. energy cutoff for muons in GeV'] = h[61]
    d['kin. energy cutoff for electrons in GeV'] = h[62]
    d['energy cutoff for photons in GeV'] = h[63]
    d['NFLAIN'] = h[64]
    d['NFLDIF'] = h[65]
    d['NFLPI0'] = h[66]
    d['NFLPIF'] = h[67]
    d['NFLCHE'] = h[68]
    d['NFRAGM'] = h[69]
    d['Earth\'s magnetic field in uT: (x,z)'] = h[70:72]
    d['flag for activating EGS4'] = h[72]
    d['flag for activating NKG'] = h[73]
    d['low-energy hadr. model flag (1.=GHEISHA, 2.=UrQMD, 3.=FLUKA)'] = h[74]
    d['high-energy hadr. model flag (0.=HDPM,1.=VENUS, 2.=SIBYLL,3.=QGSJET, 4.=DPMJET, 5.=NE X US, 6.=EPOS)'] = h[75]
    d['CERENKOV Flag (is a bitmap --> usersguide)'] = hex(int(round(h[76])))
    d['NEUTRINO flag'] = h[77]
    d['CURVED flag (0=standard, 2=CURVED)'] = h[78]
    d['computer flag (3=UNIX, 4=Macintosh)'] = h[79]
    d['theta interval (in degree): (lower, upper edge) '] = h[80:82]
    d['phi interval (in degree): (lower, upper edge) '] = h[82:84]
    d['Cherenkov bunch size in the case of Cherenkov calculations'] = h[84]
    d['number of Cherenkov detectors in (x, y) direction'] = h[85:87]
    d['grid spacing of Cherenkov detectors in cm (x, y) direction'] = h[87:89]
    d['length of each Cherenkov detector in cm in (x, y) direction'] = h[89:91]
    d['Cherenkov output directed to particle output file (= 0.) or Cherenkov output file (= 1.)'] = h[91]
    d['angle (in rad) between array x-direction and magnetic north'] = h[92]
    d['flag for additional muon information on particle output file'] = h[93]
    d['step length factor for multiple scattering step length in EGS4'] = h[94]
    d['Cherenkov bandwidth in nm: (lower, upper) end'] = h[95:97]
    num_reuse=h[97]
    d['number i of uses of each Cherenkov event'] = num_reuse
    core_x = h[98:98+num_reuse]
    core_y = h[118:118+num_reuse]
    d['core location for scattered events in cm: (x,y)'] = np.vstack((core_x,core_y)).transpose()
    d['SIBYLL interaction flag (0.= no SIBYLL, 1.=vers.1.6; 2.=vers.2.1)'] = h[138]
    d['SIBYLL cross-section flag (0.= no SIBYLL, 1.=vers.1.6; 2.=vers.2.1)'] = h[139]
    d['QGSJET interact. flag (0.=no QGSJET, 1.=QGSJETOLD,2.=QGSJET01c, 3.=QGSJET-II)'] = h[140]
    d['QGSJET X-sect. flag (0.=no QGSJET, 1.=QGSJETOLD,2.=QGSJET01c, 3.=QGSJET-II)'] = h[141]
    d['DPMJET interaction flag (0.=no DPMJET, 1.=DPMJET)'] = h[142]
    d['DPMJET cross-section flag (0.=no DPMJET, 1.=DPMJET)'] = h[143]
    d['VENUS/NE X US/EPOS cross-section flag (0=neither, 1.=VENUSSIG,2./3.=NEXUSSIG, 4.=EPOSSIG)'] = h[144]
    d['muon multiple scattering flag (1.=Moliere, 0.=Gauss)'] = h[145]
    d['NKG radial distribution range in cm'] = h[146]
    d['EFRCTHN energy fraction of thinning level hadronic'] = h[147]
    d['EFRCTHN x THINRAT energy fraction of thinning level em-particles'] = h[148]
    d['actual weight limit WMAX for thinning hadronic'] = h[149]
    d['actual weight limit WMAX x WEITRAT for thinning em-particles'] = h[150]
    d['max. radius (in cm) for radial thinning'] = h[151]
    d['viewing cone VIEWCONE (in deg): (inner, outer) angle'] = h[152:154]
    d['transition energy high-energy/low-energy model (in GeV)'] = h[154]
    d['skimming incidence flag (0.=standard, 1.=skimming)'] = h[155]
    d['altitude (cm) of horizontal shower axis (skimming incidence)'] = h[156]
    d['starting height (cm)'] = h[157]
    d['flag indicating that explicite charm generation is switched on'] = h[158]
    d['flag for hadron origin of electromagnetic subshower on particle tape'] = h[159]
    d['flag for observation level curvature (CURVOUT) (0.=flat, 1.=curved)'] = h[167]
    return d


def parse_corsika_run_header(run_header):
    '''
    parse the run header of a corsika file into a dict

    **this function is called by parseByteStringToDict()** and a user normally
    does not need to call this function directly.

    The run header of a corsika file is a 272 float list,
    where each number has a meaning by its position in the list.
    This is documented in the Corsika Manual.
    this is just moving the plain 272-float numbers from the original
    header int a dict.
    Not sure, if the key naming is well done :-/
    '''
    h = run_header
    d = dict()
    d['run number'] = h[1]
    d['date of begin run'] = int(round(h[2]))
    d['version of program'] = h[3]
    n_obs_levels = int(round(h[4]))
    if (n_obs_levels < 1) or (n_obs_levels > 10):
        ValueException('number of observation levels n must be 0 < n < 11, but is: '+str(h[4]))
    d['observation levels']=h[5:5+n_obs_levels]
    d['slope of energy spektrum']=h[15]
    d['energy range']=h[16:18]
    d['flag for EGS4 treatment of em. component'] = h[18]
    d['flag for NKG treatment of em. component'] = h[19]
    d['kin. energy cutoff for hadrons in GeV'] = h[20]
    d['kin. energy cutoff for muons in GeV'] = h[21]
    d['kin. energy cutoff for electrons in GeV'] = h[22]
    d['energy cutoff for photons in GeV'] = h[23]
    d['phyiscal constants'] = h[24:74]
    d['X-displacement of inclined observation plane'] = h[74]
    d['Y-displacement of inclined observation plane'] = h[75]
    d['Z-displacement of inclined observation plane'] = h[76]
    d['theta angle of normal vector of inclined observation plane'] = h[77]
    d['phi angle of normal vector of inclined observation plane'] = h[78]
    # now some constants, I don't understand
    d['CKA'] = h[94:134]
    d['CETA'] = h[134:139]
    d['CSTRBA'] = h[139:150]
    d['scatter range in x direction for Cherenkov'] = h[247]
    d['scatter range in y direction for Cherenkov'] = h[248]
    d['HLAY'] = h[249:254]
    d['AATM'] = h[254:259]
    d['BATM'] = h[259:264]
    d['CATM'] = h[264:269]
    d['NFLAIN'] = h[269]
    d['NFLDIF'] = h[270]
    d['NFLPI0 + 100 x NFLPIF'] = h[271]
    d['NFLCHE + 100 x NFRAGM'] = h[272]
    return d


iact_types = {
    1200: read_type_1200,
    1201: read_type_1201,
    1202: read_type_1202,
    1203: read_type_1203,
    1212: read_type_1212,
    1209: read_type_1209,
    1210: read_type_1210,
    1204: read_type_1204,
}
