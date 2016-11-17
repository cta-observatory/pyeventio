import struct
from collections import namedtuple
import gzip

import logging
import warnings
import io

from .exceptions import WrongTypeException
from .tools import read_from

log = logging.getLogger(__name__)

known_objects = {}

class EventIOFile:

    def __init__(self, path):
        log.info('Opening new file {}'.format(path))
        self.path = path
        self.__file = open(path, 'rb')

        if path.endswith('.gz'):
            log.info('Found gzipped file')
            self.__compfile = gzip.GzipFile(mode='r', fileobj=self.__file)
            self.__filehandle = io.BufferedReader(self.__compfile)
        else:
            log.info('Found uncompressed file')
            self.__filehandle = self.__file

        self.objects = read_all_headers(self, toplevel=True)
        log.info('File contains {} top level objects'.format(len(self.objects)))

    def __len__(self):
        return len(self.objects)

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
        self.__file.close()

    def __getitem__(self, idx):
        return self.objects[idx]

    def __iter__(self):
        return iter(self.objects)

    def __repr__(self):
        r = '{}(path={}, objects=[\n'.format(self.__class__.__name__, self.path)

        if len(self.objects) <= 8:
            for o in self.objects:
                r += '  {}\n'.format(o)
        else:
            for o in self.objects[:4]:
                r += '  {}\n'.format(o)
            r += '\t...\n'
            for o in self.objects[-4:]:
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

        self.objects = []

        if self.header.only_sub_objects:
            self.objects = read_all_headers(self, toplevel=False)

    def __getitem__(self, idx):
        return self.objects[idx]

    def parse_data_field(self):
        ''' Read the data in this field

        should return nice python objects, e.g. structured numpy arrays
        '''
        raise NotImplementedError

    def __repr__(self):
        if len(self.objects) > 0:
            subitems = ', subitems={}'.format(len(self.objects))
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
        first, *last = super().__repr__().split('(first')

        return '{}[{}](first'.format(
            self.__class__.__name__, self.eventio_type
        ) + ''.join(last)

SYNC_MARKER_INT_VALUE = -736130505

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
    if toplevel is True:
        sync = f.read(4)
        endianness = parse_sync_bytes(sync)
        level = 0
    else:
        endianness = f.header.endianness
        level = f.header.level + 1

    if endianness == '>':
        raise NotImplementedError('Big endian byte order is not supported by this reader')

    type_version_field = read_type_field(f)
    id_field = read_from('<I', f)[0]
    only_sub_objects, length = read_length_field(f)

    if type_version_field.extended:
        length += read_extension(f)

    data_field_first_byte = f.tell()
    return_value = (
        endianness,
        type_version_field.type,
        type_version_field.version,
        type_version_field.user,
        type_version_field.extended,
        only_sub_objects,
        length,
        id_field,
        data_field_first_byte,
        level,
    )

    return return_value


HeaderBase = namedtuple(
    'HeaderBase',
    [
        'endianness', 'type', 'version', 'user', 'extended',
        'only_sub_objects',  'length', 'id', 'data_field_first_byte',
        'level'
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
            eventio_file_or_object.seek(header.length, 1)
        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break

    return objects


# The following functions perform bit magic.
# they extract some N-bit words and 1-bit 'flags' from 32bit words
# So we need '(LEN)GTH' and '(POS)ITION' to find and extract them.
# both LEN and POS are measured in bits.
# POS starts at zero of course.

TYPE_LEN = 16
TYPE_POS = 0

USER_LEN = 1
USER_POS = 16

EXTENDED_LEN = 1
EXTENDED_POS = 17

VERSION_LEN = 12
VERSION_POS = 20

ONLYSUBOBJECTS_LEN = 1
ONLYSUBOBJECTS_POS = 30

LENGTH_LEN = 30
LENGTH_POS = 0

EXTENSION_LEN = 12
EXTENSION_POS = 0


def bool_bit_from_pos(uint32_word, pos):
    return bool(uint32_word & (1 << pos))


def len_bits_from_pos(uint32_word, len, pos):
    return (uint32_word >> pos) & ((1 << len)-1)

TypeInfo = namedtuple('TypeInfo', 'type version user extended')

def read_type_field(f):
    uint32_word = read_from('<I', f)[0]
    _type = len_bits_from_pos(uint32_word, TYPE_LEN, TYPE_POS)
    user_bit = bool_bit_from_pos(uint32_word, USER_POS)
    extended = bool_bit_from_pos(uint32_word, EXTENDED_POS)
    version = len_bits_from_pos(uint32_word, VERSION_LEN, VERSION_POS)
    return TypeInfo(_type, version, user_bit, extended)


def read_length_field(f):
    uint32_word = read_from('<I', f)[0]
    only_sub_objects = bool_bit_from_pos(uint32_word, ONLYSUBOBJECTS_POS)
    length = len_bits_from_pos(uint32_word, LENGTH_LEN, LENGTH_POS)
    return only_sub_objects, length


def read_extension(f):
    uint32_word = read_from('<I', f)[0]
    extension = len_bits_from_pos(uint32_word, EXTENSION_LEN, EXTENSION_POS)
    # we push the length-extension so many bits to the left,
    # i.e. we multiply with such a high number, that we can simply
    # use the += operator further up in `ObjectHeader_from_file` to
    # combine the normal (small) length and this extension.
    extension <<= LENGTH_LEN
    return extension
