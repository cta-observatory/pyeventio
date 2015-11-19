"""
eventio
"""
from __future__ import absolute_import
import struct
import mmap
from collections import namedtuple, OrderedDict

import numpy as np
from .tools import unpack_from, read_ints, WrongTypeException

from .header import Header
from . import photonbunches as pb
from . import tools


def parse_MmcsEventHeader(event_header):
    """ parse the event header of a corsika file into a dict
    
        **this function is called by parseByteStringToDict()** and a user normally 
        does not need to call this function directly.

        The event header of a corsika file is a 272 float list, 
        where each number has a meaning by its position in the list.
        This is documented in the Corsika Manual.
        this is just moving the plain 272-float numbers from the original
        header int a dict.
        Not sure, if the key naming is well done :-/
    """
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
    d["Earth's magnetic field in uT: (x,z)"] = h[70:72]
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

def parse_MmcsRunHeader(run_header):
    """ parse the run header of a corsika file into a dict

        **this function is called by parseByteStringToDict()** and a user normally 
        does not need to call this function directly.
    
        The run header of a corsika file is a 272 float list, 
        where each number has a meaning by its position in the list.
        This is documented in the Corsika Manual.
        this is just moving the plain 272-float numbers from the original
        header int a dict.
        Not sure, if the key naming is well done :-/
    """
    h = run_header
    d = dict()
    d['run number']=h[1]
    d['date of begin run']=int(round(h[2]))
    d['version of program']=h[3]        
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
    d['phyiscal constants']=h[24:74]
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

def read_type_1200(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise Exception("read_type_1200: first n was not 273 but "+str(n))
    
    block = np.frombuffer(
        f.read(n*4), 
        dtype=np.float32, 
        count=n)

    return parse_MmcsRunHeader(block)

def read_type_1201(f, head=None):
    """ ---> write_tel_pos
    int32 ntel
    float32 x[ntel]
    float32 y[ntel]
    float32 z[ntel]
    float32 r[ntel]
    """
    ntel, = unpack_from('i', f)
    number_of_following_arrays = int((head.length - 4) / ntel /4)
    if number_of_following_arrays != 4:
        # DN: I think this cannot happen, but who knows.
        raise Exception("in read_type_1201: number_of_following_arrays is:"
            + str(number_of_following_arrays))

    tel_pos = np.zeros(ntel, dtype=[
        ('x', 'f4'), 
        ('y', 'f4'), 
        ('z', 'f4'), 
        ('r', 'f4'), 
        ])

    arrays = np.frombuffer(
            f.read(ntel*4*4), 
            dtype=np.float32, 
            count=ntel*4)
    arrays = arrays.reshape(4, ntel)
    x,y,z,r = np.vsplit(arrays, 4)

    tel_pos['x'] = x
    tel_pos['y'] = y
    tel_pos['z'] = z
    tel_pos['r'] = r

    return tel_pos
    
def read_type_1202(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise Exception("read_type_1200: first n was not 273 but "+str(n))
    
    block = np.frombuffer(
        f.read(n*4), 
        dtype=np.float32, 
        count=n)

    return parse_MmcsEventHeader(block)

def read_type_1203(f, head=None):
    """ ---> write_tel_offset

    int32 narray, 
    float32 toff, 
    float32 xoff[narray]
    float32 yoff[narray]
    maybe:
        float32 weight[narray]
    
    """
    length_first_two = 4 + 4 
    narray, toff = unpack_from('if', f)
    number_of_following_arrays = int((head.length - length_first_two) / narray /4)
    if number_of_following_arrays not in [2, 3]:
        # DN: I think this cannot happen, but who knows.
        raise Exception("in read_type_1203: number_of_following_arrays is:"
            + str(number_of_following_arrays))

    xoff = np.frombuffer(
        f.read(narray*4), 
        dtype=np.float32, 
        count=narray)
    yoff = np.frombuffer(
        f.read(narray*4), 
        dtype=np.float32, 
        count=narray)

    weight = np.ones(
            narray, 
            dtype=np.float32)

    if number_of_following_arrays == 3:
        weight = np.frombuffer(
            f.read(narray*4), 
            dtype=np.float32, 
            count=narray)        

    return narray, toff, xoff, yoff, weight

def read_type_1204(f, head=None, headers_only=True):
    if not head.only_sub_objects:
        raise Exception("Type 1204 ususally has only sub objects, this one has not!!")
    return  list(pb.photon_bunches(f, headers_only=headers_only))

def read_type_1209(f, head=None):
    n, = read_ints(1, f)
    if n != 273:
        raise Exception("read_type_1209: first n was not 273 but "+str(n))

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

def read_any_type(f, head=None):
    f.read(head.length)
    return None

known_types = {
    1200 : read_type_1200,
    1201 : read_type_1201,
    1202 : read_type_1202,
    1203 : read_type_1203,
    1212 : read_type_1212,
    1209 : read_type_1209,
    1210 : read_type_1210,
    1204 : read_type_1204,
}

class EventIoFile_Stupid(object):

    def __init__(self, path):
        self._f = open(path)
        self.__read_meta = []
        self.__is_first_event_already_read = False
        # these functions *must* be called in this order, 
        # since this is the order, the data is in the file.
        self.__read_run_header()
        self.__read_input_card()
        self.__read_tel_pos()
        before_first_header = self._f.tell()
        self.__read_event_header()
        self.__read_tel_offset()
        self._f.seek(before_first_header)

    def __read_run_header(self):
        head = read_header(self._f)
        if not head.type == 1200:
            raise ValueError("Expected Header with type=1200, but found "+str(head.type))
        self.run_header = read_type_1200(self._f, head)
        self.__read_meta.append(head)

    def __read_input_card(self):
        head = read_header(self._f)
        if not head.type == 1212:
            raise ValueError("Expected Header with type=1212, but found "+str(head.type))
        self.input_card = read_type_1212(self._f, head)
        self.__read_meta.append(head)

    def __read_tel_pos(self):
        head = read_header(self._f)
        if not head.type == 1201:
            raise ValueError("Expected Header with type=1201, but found "+str(head.type))
        self.tel_pos = read_type_1201(self._f, head)
        self.__read_meta.append(head)

    def __read_event_header(self):
        head = read_header(self._f)
        if not head.type == 1202:
            raise ValueError("Expected Header with type=1202, but found "+str(head.type))
        self.event_header = read_type_1202(self._f, head)
        self.__read_meta.append(head)

    def __read_tel_offset(self):
        head = read_header(self._f)
        if not head.type == 1203:
            raise ValueError("Expected Header with type=1203, but found "+str(head.type))
        self.tel_offset = read_type_1203(self._f, head)
        self.__read_meta.append(head)
    
    def __read_photon_bunches(self):
        head = read_header(self._f)
        if not head.type == 1204:
            raise ValueError("Expected Header with type=1204, but found "+str(head.type))
        self.photon_bunches, self.subhead = read_type_1204(self._f, head)
        self.__read_meta.append(head)
        
    def __read_event_end(self):
        head = read_header(self._f)
        if not head.type == 1209:
            raise ValueError("Expected Header with type=1209, but found "+str(head.type))
        self.event_end = read_type_1209(self._f, head)
        self.__read_meta.append(head)
        
    def __iter__(self):
        return self

    def next(self):
        #try: 
            self.__read_event_header()
            if not self.__is_first_event_already_read:
                self.__read_tel_offset()
                self.__is_first_event_already_read = True
            self.__read_photon_bunches()
            self.__read_event_end()
            return self.photon_bunches

        #except ValueError:
            #raise StopIteration


class EventIoFile(object):

    def __init__(self, path, debug=False):
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)
        self.__header_list = []

        self.run_header = self.__read_run_header()
        self._make_complete_header_list()
        self._make_reuse_header_list()
        self.__mm.seek(0)
        self.__read_run_header()

    @property
    def header_list(self):
        return self.__header_list
    

    def _make_complete_header_list(self):
        while True:
            try:
                header = self.__get_and_save_header()
            except struct.error:
                break
            self.__mm.seek(header.length, 1)

    def _make_reuse_header_list(self):
        for i, h in enumerate(self.__header_list[:]):
            if h.type == 1204:
                self.__mm.seek(h.tell)
                photon_bunch_headers = read_type_1204(self.__mm, h, headers_only=True)
                self.__header_list[i] = (h, photon_bunch_headers)

    def __get_and_save_header(self, expect_type=None):
        header = Header(self.__mm)
        if not expect_type is None:
            if header.type != expect_type:
                header_length = 4 if not header.extended else 5
                self.__mm.seek(header_length * -4, 1)
                raise WrongTypeException(
                    "expected ", expect_type, 
                    ", got:", header.type)


        #self.__header_list.append(header)
        return header

    def __get_type(self, type):
        header = self.__get_and_save_header(expect_type=type)
        return known_types[type](self.__mm, header)


    def __read_run_header(self):
        rh = self.__get_type(1200)
        rh['input_card'] = self.__get_type(1212)
        rh['tel_pos'] = self.__get_type(1201)

        return rh

    def __read_event_header(self):
        self.current_event_header = self.__get_type(1202)        
        self.current_event_header['telescope_offsets'] = self.__get_type(1203)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        while True:
            try:
                return pb.PhotonBundle(self.__mm)
            except WrongTypeException:
                pass
            
            try:
                _ = self.__get_and_save_header(expect_type=1204)
                # simply get rid of the 1204-inter-reuse-stuff.
                #_ = self.__get_type(1204)
            except (WrongTypeException, ValueError):
                pass

            try:
                self.__read_event_header()
            except (WrongTypeException, ValueError):
                pass

            try:
                self.last_event_end = self.__get_type(1209)
            except (WrongTypeException, ValueError):
                pass            

            try:
                self.run_end = self.__get_type(1210)
                raise StopIteration
            except (WrongTypeException, ValueError):
                pass
                
class EventIoFileStream(object):

    def __init__(self, path, debug=False):
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        self.run_header = self.__read_run_header()

    def __read_run_header(self):
        rh = self._retrieve_payload_of_type(1200)
        rh['input_card'] = self._retrieve_payload_of_type(1212)
        rh['tel_pos'] = self._retrieve_payload_of_type(1201)
        return rh

    def _retrieve_payload_of_type(self, type):
        header = self.__get_header(expect_type=type)
        return known_types[type](self.__mm, header)

    def __get_header(self, expect_type):
        header = Header(self.__mm)
        if header.type != expect_type:
            header_length = 4 if not header.extended else 5
            self.__mm.seek(header_length * -4, 1)
            raise WrongTypeException(
                "expected ", expect_type, 
                ", got:", header.type)
        return header


    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        while True:
            try:
                return pb.PhotonBundle(self.__mm)
            except WrongTypeException:
                pass
            
            try:
                _ = self.__get_header(expect_type=1204)
                # simply get rid of the 1204-inter-reuse-stuff.
            except (WrongTypeException, ValueError):
                pass

            try:
                self.__read_event_header()
            except (WrongTypeException, ValueError):
                pass

            try:
                self.last_event_end = self._retrieve_payload_of_type(1209)
            except (WrongTypeException, ValueError):
                pass            

            try:
                self.run_end = self._retrieve_payload_of_type(1210)
                raise StopIteration
            except (WrongTypeException, ValueError):
                pass
                
    def __read_event_header(self):
        self.current_event_header = self._retrieve_payload_of_type(1202)        
        self.current_event_header['telescope_offsets'] = self._retrieve_payload_of_type(1203)
