''' Methods to read in and parse the IACT EventIO object types '''
import struct
import numpy as np
from numpy.lib.recfunctions import append_fields

from ..tools import read_ints, read_from, read_eventio_string
from ..base import EventIOObject
from ..exceptions import WrongSizeException
from .parse_corsika_data import (
    parse_corsika_event_header,
    parse_corsika_run_header,
)


__all__ = [
    'CORSIKARunHeader',
    'CORSIKATelescopeDefinition',
    'CORSIKAEventHeader',
    'CORSIKAArrayOffsets',
    'CORSIKATelescopeData',
    'IACTPhotons',
    'IACTLayout',
    'IACTTriggerTime',
    'IACTPhotoElectrons',
    'CORSIKAEventEndBlock',
    'CORSIKARunEndBlock',
    'CORSIKALongitudinal',
    'CORSIKAInputCard',
]


class CORSIKARunHeader(EventIOObject):
    '''
    This object contains the corsika run header block
    '''
    eventio_type = 1200

    def parse_data_field(self):
        '''
        Read the data in this EventIOItem

        Returns a dictionary with the items of the CORSIKA run header block
        '''
        self.seek(0)
        data = self.read()
        n, = struct.unpack('i', data[:4])
        if n != 273:
            raise WrongSizeException(
                'Expected 273 bytes, but found {}'.format(n))

        block = np.frombuffer(
            data,
            dtype=np.float32,
            count=n,
            offset=4,
        )
        return parse_corsika_run_header(block)


class CORSIKATelescopeDefinition(EventIOObject):
    '''
    This object contains the coordinates of the telescopes
    of the simulated array
    '''
    eventio_type = 1201

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.n_telescopes, = read_ints(1, self)

    def __len__(self):
        return self.n_telescopes

    def parse_data_field(self):
        '''
        Read the data in this EventIOItem

        Returns a structured numpy array with columns (x, y, z, r)
        with a row for each telescope
        '''
        self.seek(4)
        data = self.read()

        number_of_following_arrays = len(data) // (self.n_telescopes * 4)
        if number_of_following_arrays != 4:
            # DN: I think this cannot happen, but who knows.
            msg = 'Number_of_following_arrays is: {}'
            raise Exception(msg.format(number_of_following_arrays))

        dtype = np.dtype('float32')
        block = np.frombuffer(
            data,
            dtype=dtype,
            count=self.n_telescopes * dtype.itemsize,
        )
        tel_pos = np.core.records.fromarrays(
            block.reshape(4, self.n_telescopes),
            names=['x', 'y', 'z', 'r'],
        )

        return tel_pos


class CORSIKAEventHeader(EventIOObject):
    ''' This Object contains the CORSIKA event header block '''
    eventio_type = 1202

    def parse_data_field(self):
        '''
        Read the data in this EventIOItem

        Returns a dictionary containing the keys of the
        CORSIKA event header block
        '''
        self.seek(0)
        data = self.read()
        n, = struct.unpack('i', data[:4])
        if n != 273:
            raise WrongSizeException(
                'Expected 273 bytes, but found {}'.format(n))

        block = np.frombuffer(
            data,
            dtype=np.float32,
            count=n,
            offset=4,
        )

        return parse_corsika_event_header(block)


class CORSIKAArrayOffsets(EventIOObject):
    eventio_type = 1203

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.n_arrays, = read_ints(1, self)
        self.time_offset, = read_from('f', self)
        self.n_reuses = self.n_arrays

    def parse_data_field(self):
        '''
        Read the data in this EventIOItem

        Returns a structured numpy array with columns (t, x, y, weight)
        with a row for each array. This object is used to store the
        array position and contains one set of coordinates for each reuse.
        '''
        self.seek(8)
        data = self.read()

        n_columns = len(data) / (self.n_arrays * 4)
        assert n_columns.is_integer()
        n_columns = int(n_columns)
        if n_columns not in (2, 3):
            # dneise: I think this cannot happen, but who knows.
            msg = 'Number of offset columns should be in 2 or 3, found {}'
            raise Exception(msg.format(n_columns))

        positions = np.frombuffer(
            data,
            dtype=np.float32,
            count=self.n_arrays * n_columns,
        ).reshape(n_columns, self.n_arrays)

        if n_columns == 3:
            weights = positions[3, :]
        else:
            weights = np.ones(self.n_arrays, dtype=np.float32)

        return np.core.records.fromarrays(
            [positions[0, :], positions[1, :], weights],
            names=['x', 'y', 'weight'],
        )


class CORSIKATelescopeData(EventIOObject):
    '''
    A container class for the photon bunches.
    Usually contains one photon bunch object (IACTPhotons)
    per simulated telescope
    '''
    eventio_type = 1204


class IACTPhotons(EventIOObject):
    '''
    This object contains the data of the simulated cherenkov photons
    for a single telescope
    '''
    eventio_type = 1205
    columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda')

    def __init__(self, header, parent):
        super().__init__(header, parent)
        self.compact = bool(self.header.version // 1000 == 1)

        (
            self.array,
            self.telescope,
            self.n_photons,
            self.n_bunches
        ) = read_from('hhfi', self)

    def __repr__(self):
        return '{}(length={}, n_bunches={})'.format(
            self.__class__.__name__,
            self.header.length,
            self.n_bunches,
        )

    def parse_data_field(self):
        '''
        Read the data in this EventIOObject

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

        if self.compact:
            dtype = np.dtype('int16')
        else:
            dtype = np.dtype('float32')

        if self.n_bunches == 0:
            return np.array([], dtype=[(col, dtype) for col in self.columns])

        self.seek(12)
        block = np.frombuffer(
            self.read(self.n_bunches * len(self.columns) * dtype.itemsize),
            dtype=dtype,
            count=self.n_bunches * len(self.columns)
        )
        block = block.reshape(self.n_bunches, len(self.columns))

        bunches = np.core.records.fromrecords(
            block,
            names=self.columns,
        )

        if self.compact:
            bunches = bunches.astype([(c, 'float32') for c in self.columns])
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
            bunches['zem'] = np.power(10., bunches['zem'] * 0.001)
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


class IACTLayout(EventIOObject):
    eventio_type = 1206


class IACTTriggerTime(EventIOObject):
    eventio_type = 1207


class IACTPhotoElectrons(EventIOObject):
    eventio_type = 1208


class CORSIKAEventEndBlock(EventIOObject):
    eventio_type = 1209

    def parse_data_field(self):
        self.seek(0)
        n, = read_ints(1, self)
        if n != 273:
            raise WrongSizeException(
                'Expected 273 bytes, but found {}'.format(n))

        dtype = np.dtype('float32')
        block = np.frombuffer(
            self.read(n * dtype.itemsize),
            dtype=dtype,
            count=n,
        )

        return block


class CORSIKARunEndBlock(EventIOObject):
    ''' This Object contains the CORSIKA run end block '''
    eventio_type = 1210

    def parse_data_field(self):
        '''
        Read the data in this EventIOObject

        Returns the CORSIKA run end block as arrays of floats.
        No parsing yet, sorry. The meaning is defined in the CORSIKA
        User Guide.
        '''

        self.seek(0)
        n, = read_ints(1, self)

        dtype = np.dtype('float32')
        block = np.frombuffer(
            self.read(n * dtype.itemsize),
            dtype=dtype,
            count=n,
        )

        return block


class CORSIKALongitudinal(EventIOObject):
    ''' This Object contains the CORSIKA longitudinal shower data block '''
    eventio_type = 1211

    def __init__(self, header, parent):
        super().__init__(header, parent)

    def parse_data_field(self):
        '''
        Read the data in this EventIOObject

        Returns the CORSIKA longitudinal shower data block as arrays of floats.
        No parsing yet, sorry. The meaning is defined in the CORSIKA
        User Guide.
        '''
        self.seek(0)
        long = {}
        long['event_id'], = read_ints(1, self)
        long['type'], = read_ints(1, self)
        long['np'], = read_from('<h', self)
        long['nthick'], = read_from('<h', self)
        long['thickstep'], = read_from('<f', self)
        long['data'] = np.frombuffer(
            self.read(4 * long['np'] * long['nthick']),
            dtype='<f4'
        ).reshape(long['np'], long['nthick'])

        return long


class CORSIKAInputCard(EventIOObject):
    ''' This Object contains the CORSIKA steering card '''
    eventio_type = 1212

    def parse_data_field(self):
        '''
        Read the data in this EventIOObject

        Returns the CORSIKA steering card as string.
        '''
        self.seek(0)
        n_strings, = read_from('<i', self)
        input_card = bytearray()
        for i in range(n_strings):
            input_card.extend(read_eventio_string(self))
            input_card.append(ord('\n'))
        return input_card


def remove_ascii_control_characters(string):
    ''' See http://stackoverflow.com/a/4324823/3838691 '''
    mapping = dict.fromkeys(range(32))
    return string.translate(mapping)
