''' Methods to read in and parse the IACT EventIO object types '''
import numpy as np
import struct

from ..tools import read_ints, read_from
from ..base import EventIOObject, known_objects
from ..exceptions import WrongSizeException
from .parse_corsika_data import (
    parse_corsika_event_header,
    parse_corsika_run_header,
)


__all__ = [
    'iact_types',
]


class CorsikaRunHeader(EventIOObject):
    eventio_type = 1200

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.run_header = self.parse_data_field()

    def __getitem__(self, key):
        return self.run_header[key]

    def parse_data_field(self):
        self.seek(0)
        data = self.read()
        n, = struct.unpack('i', data[:4])
        if n != 273:
            raise WrongSizeException('Expected 273 bytes, but found {}'.format(n))

        block = np.frombuffer(
            data,
            dtype=np.float32,
            count=n,
            offset=4,
        )
        return parse_corsika_run_header(block)


class CorsikaTelescopeDefinition(EventIOObject):
    eventio_type = 1201

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.num_telescopes, self.telescope_positions = self.parse_data_field()

    def __getitem__(self, idx):
        return self.telescope_positions[idx]

    def __len__(self):
        return self.num_telescopes

    def parse_data_field(self):
        ''' ---> write_tel_pos
        int32 ntel
        float32 x[ntel]
        float32 y[ntel]
        float32 z[ntel]
        float32 r[ntel]
        '''
        self.seek(0)
        data = self.read()

        n_tel, = struct.unpack('i', data[:4])
        number_of_following_arrays = int((self.header.length - 4) / n_tel / 4)
        if number_of_following_arrays != 4:
            # DN: I think this cannot happen, but who knows.
            msg = 'Number_of_following_arrays is: {}'
            raise Exception(msg.format(number_of_following_arrays))

        tel_pos = np.empty(
            n_tel,
            dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('r', 'f4')],
        )

        arrays = np.frombuffer(
            data,
            dtype=np.float32,
            count=n_tel * 4,
            offset=4,
        )
        arrays = arrays.reshape(4, n_tel)
        x, y, z, r = np.vsplit(arrays, 4)

        tel_pos['x'] = x
        tel_pos['y'] = y
        tel_pos['z'] = z
        tel_pos['r'] = r

        return n_tel, tel_pos


class CorsikaEventHeader(EventIOObject):
    eventio_type = 1202

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.event_header = self.parse_data_field()

    def __getitem__(self, key):
        return self.event_header[key]

    def parse_data_field(self):
        self.seek(0)
        data = self.read()
        n, = struct.unpack('i', data[:4])
        if n != 273:
            raise WrongSizeException('Expected 273 bytes, but found {}'.format(n))

        block = np.frombuffer(
            data,
            dtype=np.float32,
            count=n,
            offset=4,
        )

        return parse_corsika_event_header(block)


class CorsikaTelescopeOffsets(EventIOObject):
    eventio_type = 1203

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.n_offsets, self.telescope_offsets = self.parse_data_field()

    def __getitem__(self, idx):
        return self.telescope_offsets[idx]

    def parse_data_field(self):
        ''' ---> write_tel_offset

        int32 narray,
        float32 toff,
        float32 xoff[narray]
        float32 yoff[narray]
        maybe:
            float32 weight[narray]

        '''
        self.seek(0)
        data = self.read()
        length_first_two = 4 + 4
        n_offsets, toff = struct.unpack('if', data[:length_first_two])
        number_arrays = (len(data) - length_first_two) // (n_offsets * 4)
        if number_arrays not in (2, 3):
            # dneise: I think this cannot happen, but who knows.
            msg = 'Number of offset arrays should be in 3 or 4, found {}'
            raise Exception(msg.format(number_arrays))

        positions = np.frombuffer(
            data,
            dtype=np.float32,
            count=n_offsets * number_arrays,
            offset=length_first_two,
        ).reshape(number_arrays, -1)

        if number_arrays == 3:
            weights = positions[2]
        else:
            weights = np.ones(n_offsets, dtype=np.float32)

        offsets = np.core.records.fromarrays(
            [positions[0], positions[1], weights],
            names=['x', 'y', 'weight'],
        )

        return n_offsets, offsets


class CorsikaTelescopeData(EventIOObject):
    eventio_type = 1204


class IACTPhotons(EventIOObject):
    eventio_type = 1205

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.compact = bool(self.header.version // 1000 == 1)

        self.array, self.telescope, self.photons, self.n_bunches = read_from('hhfi', self)
        self.bunches = self.parse_data_field()

    def __getitem__(self, idx):
        return self.bunches[idx]

    def __repr__(self):
        return '{}(first={}, length={}, n_bunches={})'.format(
            self.__class__.__name__,
            self.first_byte,
            self.header.length,
            self.n_bunches,
        )

    def parse_data_field(self):
        self.seek(12)

        columns = ('x', 'y', 'cx', 'cy', 'time', 'zem', 'photons', 'lambda')

        if self.compact:
            dtype = np.dtype('int16')
        else:
            dtype = np.dtype('float32')

        block = np.frombuffer(
            self.read(self.n_bunches * len(columns) * dtype.itemsize),
            dtype=dtype,
            count=self.n_bunches * len(columns)
        )
        block = block.reshape(self.n_bunches, len(columns))

        bunches = np.core.records.fromrecords(
            block,
            names=columns,
        )

        if self.compact:
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

        return bunches


class IACTLayout(EventIOObject):
    eventio_type = 1206


class IACTTriggerTime(EventIOObject):
    eventio_type = 1207


class IACTPhotoElectrons(EventIOObject):
    eventio_type = 1208


class CorsikaEventEndBlock(EventIOObject):
    eventio_type = 1209

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.event_end_data = self.parse_data_field()

    def __getitem__(self, idx):
        return self.event_end_data[idx]

    def parse_data_field(self):
        self.seek(0)
        n, = read_ints(1, self)
        if n != 273:
            raise WrongSizeException('Expected 273 bytes, but found {}'.format(n))

        dtype = np.dtype('float32')
        block = np.frombuffer(
            self.read(n * dtype.itemsize),
            dtype=dtype,
            count=n,
        )

        return block


class CorsikaRunEndBlock(EventIOObject):
    eventio_type = 1210

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.run_end_data = self.parse_data_field()

    def __getitem__(self, idx):
        return self.run_end_data[idx]

    def parse_data_field(self):
        self.seek(0)
        n, = read_ints(1, self)

        dtype = np.dtype('float32')
        block = np.frombuffer(
            self.read(n * dtype.itemsize),
            dtype=dtype,
            count=n,
        )

        return block


class CorsikaLongitudinal(EventIOObject):
    eventio_type = 1211

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.longitudinal_data = self.parse_data_field()

    def __getitem__(self, idx):
        return self.longitudinal_data[idx]

    def parse_data_field(self):
        self.seek(0)
        n, = read_ints(1, self)

        dtype = np.dtype('float32')
        block = np.frombuffer(
            self.read(n * dtype.itemsize),
            dtype=dtype,
            count=n,
        )

        return block


class CorsikaInputCard(EventIOObject):
    eventio_type = 1212

    def __init__(self, eventio_file, header, first_byte):
        super().__init__(eventio_file, header, first_byte)
        self.input_card = self.parse_data_field()

    def parse_data_field(self):
        self.seek(0)
        return self.read().decode()


known_objects.update({
    o.eventio_type: o
    for o in [
        CorsikaRunHeader,
        CorsikaTelescopeDefinition,
        CorsikaEventHeader,
        CorsikaTelescopeOffsets,
        CorsikaTelescopeData,
        IACTPhotons,
        IACTLayout,
        IACTTriggerTime,
        IACTPhotoElectrons,
        CorsikaEventEndBlock,
        CorsikaRunEndBlock,
        CorsikaLongitudinal,
        CorsikaInputCard,
    ]
})
