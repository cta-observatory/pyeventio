import struct
from collections import namedtuple
import mmap
import gzip

import logging
import warnings

from .tools import read_ints
from .exceptions import WrongTypeException

log = logging.getLogger(__name__)

TypeInfo = namedtuple('TypeInfo', 'type version user extended')
SYNC_MARKER_INT_VALUE = -736130505

known_objects = {}


class EventIOFile:

    def __init__(self, path, debug=False):
        log.info('Opening new file {}'.format(path))
        self.path = path
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        if path.endswith('.gz'):
            log.info('Found gzipped file')
            self.__compfile = gzip.GzipFile(mode='r', fileobj=self.__mm)
            self.__filehandle = self.__compfile
        else:
            log.info('Found uncompressed file')
            self.__filehandle = self.__mm

        self.__objects = read_all_headers(self, toplevel=True)

    def __len__(self):
        return len(self.__objects)

    def seek(self, position, whence=0):
        return self.__filehandle.seek(position, whence)

    def tell(self):
        return self.__filehandle.tell()

    def read(self, size=-1):
        return self.__filehandle.read(size)

    def read_from_position(self, first_byte, size):
        pos = self.__filehandle.tell()
        self.seek(first_byte)
        data = self.read(size)
        self.seek(pos)
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__mm.close()
        self.__file.close()

    def __getitem__(self, idx):
        return self.__objects[idx]

    def __iter__(self):
        return iter(self.__objects)

    def __repr__(self):
        r = '{}(path={}, objects=[\n'.format(self.__class__.__name__, self.path)

        if len(self.__objects) <= 8:
            for o in self.__objects:
                r += '  {}\n'.format(o)
        else:
            for o in self.__objects[:4]:
                r += '  {}\n'.format(o)
            r += '\t...\n'
            for o in self.__objects[-4:]:
                r += '  {}\n'.format(o)
        r += '])'
        return r


class EventIOObject:
    eventio_type = None

    def __init__(self, eventio_file, header, first_byte):
        if header.type != self.eventio_type:
            raise WrongTypeException(self.eventio_type, header.type)

        self.eventio_file = eventio_file
        self.first_byte = first_byte
        self.header = header
        self.position = 0

        self.__objects = []

        if self.header.only_sub_objects:
            self.__objects = read_all_headers(self, toplevel=False)

    def __getitem__(self, idx):
        return self.__objects[idx]

    def parse_data_field(self):
        ''' Read the data in this field

        should return nice python objects, e.g. structured numpy arrays
        '''
        raise NotImplemented

    def __repr__(self):
        if len(self.__objects) > 0:
            subitems = ', subitems=[\n    {}\n  ]'.format(
                ',\n    '.join(str(o) for o in self.__objects)
            )
        else:
            subitems = ''

        return '{}(first={}, length={}{})'.format(
            self.__class__.__name__,
            self.first_byte,
            self.header.length,
            subitems,
        )

    def read(self, size=-1):
        if size == -1 or size > self.header.length - self.position:
            size = self.header.length - self.position

        data = self.eventio_file.read_from_position(
            first_byte=self.header.data_field_first_byte + self.position, size=size,
        )

        self.position += size

        return data

    def read_from_position(self, first_byte, size):
        pos = self.tell()
        self.seek(first_byte)
        data = self.read(size)
        self.seek(pos)
        return data

    def seek(self, offset, whence=0):
        if whence == 0:
            assert offset >= 0
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = self.header.length + offset
        else:
            raise ValueError('invalid whence ({}, should be 0, 1 or 2)'.format(whence))
        return self.position

    def tell(self):
        return self.position


class UnknownObject(EventIOObject):
    def __init__(self, eventio_file, header, first_byte):
        self.eventio_type = header.type
        super().__init__(eventio_file, header, first_byte)

    def __repr__(self):
        return '{}[{}](first={}, length={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.first_byte,
            self.header.length,
        )


def unpack_type(_type):
    t = _type & 0xffff
    version = (_type & 0xfff00000) >> 20
    user_bit = bool(_type & (1 << 16))
    extended = bool(_type & (1 << 17))
    return TypeInfo(t, version, user_bit, extended)


def unpack_length(length):
    only_sub_objects = bool(length & 1 << 30)
    # bit 31 of length is reserved
    length &= 0x3fffffff
    return only_sub_objects, length


def extend_length(extended, length):
    extended &= 0xfff
    length = length & extended << 12
    return length


def parse_sync_bytes(sync):
    ''' returns the endianness as given by the sync byte '''

    int_value, = struct.unpack('<i', sync)
    if int_value == SYNC_MARKER_INT_VALUE:
        log.debug('Found Little Endian byte order')
        return '<'

    int_value, = struct.unpack('>i', sync)
    if int_value == SYNC_MARKER_INT_VALUE:
        log.debug('Found Big Endian byte order')
        return '>'

    raise ValueError(
        'Sync must be 0xD41F8A37 or 0x378A1FD4. Got: {}'.format(sync)
    )


def read_header(f, toplevel):
    _start_point = f.tell()

    if toplevel is True:
        sync = f.read(4)
        try:
            endianness = parse_sync_bytes(sync)
        except ValueError:
            f.seek(_start_point)
            raise
    else:
        endianness = f.header.endianness

    if endianness == '>':
        raise NotImplementedError('Big endian byte order is not supported by this reader')

    _type, _id, length = read_ints(3, f)

    _type = unpack_type(_type)
    only_sub_objects, length = unpack_length(length)

    if _type.extended:
        extended, = read_ints(1, f)
        length = extend_length(extended, length)

    _tell = f.tell()
    return_value = (
        endianness,
        _type.type,
        _type.version,
        _type.user,
        _type.extended,
        only_sub_objects,
        length,
        _id,
        _tell,
    )

    return return_value


HeaderBase = namedtuple(
    'HeaderBase',
    [
        'endianness', 'type', 'version', 'user', 'extended',
        'only_sub_objects',  'length', 'id', 'data_field_first_byte'
    ]
)


class ObjectHeader(HeaderBase):
    def __new__(cls, f, parent=None):
        self = super().__new__(cls, *read_header(f, parent))
        return self


def read_all_headers(eventio_file_or_object, toplevel=True):
    eventio_file_or_object.seek(0)
    objects = []
    while True:
        position = eventio_file_or_object.tell()
        try:
            header = ObjectHeader(
                eventio_file_or_object,
                toplevel,
            )
            log.debug(
                'Found header of type {} at byte {}'.format(header.type, position)
            )
            eventio_object = known_objects.get(header.type, UnknownObject)(
                eventio_file=eventio_file_or_object,
                header=header,
                first_byte=position,
            )
            objects.append(eventio_object)
            try:
                eventio_file_or_object.seek(header.length, 1)
            except ValueError:
                warnings.warn('File seems to be truncated')
                break
        except struct.error:
            break

    return objects
