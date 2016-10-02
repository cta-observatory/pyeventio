''' Methods to read in and parse the IACT EventIO object types '''
import numpy as np
import struct

from ..tools import read_ints
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




known_objects.update({
    o.eventio_type: o
    for o in [
        CorsikaRunHeader,
        CorsikaTelescopeDefinition,
        CorsikaEventHeader,
        CorsikaTelescopeOffsets,
    ]
})
