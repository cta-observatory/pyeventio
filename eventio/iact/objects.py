''' Methods to read in and parse the IACT EventIO object types '''
import numpy as np
from numpy.lib.recfunctions import append_fields
import struct
import io

from functools import namedtuple

from .exceptions import WrongSizeException
from .parse_corsika_data import (
    parse_corsika_event_header,
    parse_corsika_run_header,
)

def make_CorsikaRunHeader(obj):
    ''' return namedtuple with items of CORSIKA run header block.'''
    assert obj[0].type == 1200

    n, = struct.unpack('i', obj[1].value[:4])
    if n != 273:
        raise WrongSizeException('Expected 273 bytes, but found {}'.format(n))

    block = np.frombuffer(
        obj[1].value[4:],
        dtype=np.float32,
        count=n,
    )
    return parse_corsika_run_header(block)


CorsikaTelescopeDefinition = namedtuple('CorsikaTelescopeDefinition', 'n_telescopes, tel_pos')
def make_CorsikaTelescopeDefinition(obj):
    '''
    This object contains the coordinates of the telescopes of the simulated array
    Read the data in this EventIOItem

    Returns a structured numpy array with columns (x, y, z, r)
    with a row for each telescope
    '''
    assert obj[0].type == 1201

    n_telescopes = struct.unpack_from('i', obj[1].value)[0]

    data = obj[1].value[4:]

    number_of_following_arrays = len(data) // (n_telescopes * 4)
    if number_of_following_arrays != 4:
        # DN: I think this cannot happen, but who knows.
        msg = 'Number_of_following_arrays is: {}'
        raise Exception(msg.format(number_of_following_arrays))

    dtype = np.dtype('float32')
    block = np.frombuffer(
        data,
        dtype=dtype,
        count=n_telescopes * dtype.itemsize,
    )
    tel_pos = np.core.records.fromarrays(
        block.reshape(4, n_telescopes),
        names=['x', 'y', 'z', 'r'],
    )
    return CorsikaTelescopeDefinition(n_telescopes, tel_pos)


def make_CorsikaEventHeader(obj):
    '''Return a namedtuple containing the keys of the CORSIKA event header block'''
    assert obj[0].type == 1202

    value = obj[1].value
    n = struct.unpack_from('i', value)[0]
    if n != 273:
        raise WrongSizeException('Expected 273 bytes, but found {}'.format(n))

    block = np.frombuffer(
        value,
        dtype=np.float32,
        count=n,
        offset=struct.calcsize('i'),
    )

    return parse_corsika_event_header(block)

CorsikaArrayOffsets = namedtuple('CorsikaArrayOffsets', 'time_offset, offsets')
def make_CorsikaArrayOffsets(obj):
    '''Return a namedtuple(time_offset, offsets)

        time_offset: a float
        offsets: structured numpy array with columns (x, y, weight)

    This object is used to store the
    array position and contains one set of coordinates for each reuse.
    '''
    assert obj[0].type == 1203

    n_arrays, time_offset = struct.unpack_from('if', obj[1].value)

    n_columns = (len(obj[1].value)-struct.calcsize('if')) / (n_arrays * 4)
    assert n_columns.is_integer()
    n_columns = int(n_columns)
    if n_columns not in (2, 3):
        # dneise: I think this cannot happen, but who knows.
        msg = 'Number of offset columns should be in 2 or 3, found {}'
        raise Exception(msg.format(n_columns))

    positions = np.frombuffer(
        obj[1].value,
        dtype=np.float32,
        count=n_arrays * n_columns,
        offset=struct.calcsize('if'),
    ).reshape(n_columns, n_arrays)

    if n_columns == 3:
        weights = positions[3, :]
    else:
        weights = np.ones(n_arrays, dtype=np.float32)

    offsets = np.core.records.fromarrays(
        [positions[0, :], positions[1, :], weights],
        names=['x', 'y', 'weight'],
    )

    return CorsikaArrayOffsets(time_offset, offsets)

def make_TelescopeEvents(obj):
    assert obj[0].type == 1204
    return [make_IACTPhotons(obj) for obj in obj[1]]


def make_IACTPhotons(obj):
    '''
    Returns a numpy structured array with a record for each photon
    and the following columns:
        x:         x coordinate in cm
        y:         y coordinate in cm
        cx:        cosine of incident angle in x direction
        cy:        cosine of incident angle in y direction
        time:      time since first interaction in ns
        zem:       Emission height in cm above sea level
        lambda:    wavelength in nm
        scattered: indicates if the photon was scattered in the atmosphere
    '''
    assert obj[0].type == 1205

    compact = bool(obj[0].version // 1000 == 1)

    array, telescope, n_photons, n_bunches = struct.unpack_from('hhfi', obj[1].value)

    if compact:
        dtype = np.dtype('int16')
    else:
        dtype = np.dtype('float32')

    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda')
    block = np.frombuffer(
        obj[1].value,
        dtype=dtype,
        count=n_bunches * len(columns),
        offset=struct.calcsize('hhfi')
    ).reshape(n_bunches, len(columns))

    bunches = np.core.records.fromrecords(
        block,
        names=columns,
    )

    if compact:
        bunches = bunches.astype([(c, 'float32') for c in columns])
        bunches['x'] *= 0.1  # now in cm
        bunches['y'] *= 0.1  # now in cm

        # if compact, cosines are scaled by a factor of 30000
        bunches['cx'] /= 30000
        bunches['cy'] /= 30000
        #   bernloehr clips in his implementation of the reader.
        #   I am not sure I really want that.
        # bunches['cx'] = bunches['cx'].clip(a_min=-1., a_max=1.)
        # bunches['cy'] = bunches['cy'].clip(a_min=-1., a_max=1.)

        bunches['time'] *= 0.1  # in nanoseconds since first interaction.
        bunches['zem'] = np.power(10., bunches['zem']*0.001)
        bunches['photons'] *= 0.01

    bunches = append_fields(
        bunches,
        data=bunches['lambda'] < 0,
        dtypes=bool,
        names='scattered',
        usemask=False,
    )
    bunches['lambda'] = np.abs(bunches['lambda'])

    return bunches

def make_float_block(obj):
    '''
    No parsing yet, sorry. The meaning is defined in the CORSIKA
    User Guide.
    '''
    return np.frombuffer(
        obj[1].value,
        dtype=np.dtype('float32'),
        count=struct.unpack_from('i', obj[1].value)[0],
        offset=struct.calcsize('i')
    )
def make_CorsikaEventEndBlock(obj):
    assert obj[0].type == 1209
    return make_float_block(obj)

def make_CorsikaRunEndBlock(obj):
    assert obj[0].type == 1210
    return make_float_block(obj)

def make_CorsikaInputCard(obj):
    '''Return the CORSIKA steering card as string.'''
    assert obj[0].type == 1212
    # corsika input card is stored as null terminated strings
    strings = obj[1].value.decode().split('\0')
    inputcard = [
        remove_ascii_control_characters(string)
        for string in strings
        if string
    ]
    return inputcard


def remove_ascii_control_characters(string, mapping=dict.fromkeys(range(32))):
    ''' See http://stackoverflow.com/a/4324823/3838691 '''
    return string.translate(mapping)
