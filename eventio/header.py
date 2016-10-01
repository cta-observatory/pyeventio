import struct
from collections import namedtuple
import logging

from .tools import read_ints

log = logging.getLogger(__name__)

TypeInfo = namedtuple('TypeInfo', 'type version user extended')
SYNC_MARKER_INT_VALUE = -736130505


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


def read_header(f, parent):
    _start_point = f.tell()

    if parent is None:
        sync = f.read(4)
        try:
            endianness = parse_sync_bytes(sync)
        except ValueError:
            f.seek(_start_point)
            raise
    else:
        endianness = parent.header.endianness

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
    'endianness type version user extended only_sub_objects length id tell'
)


class ObjectHeader(HeaderBase):
    def __new__(cls, f, parent=None):
        self = super().__new__(cls, *read_header(f, parent))
        return self
