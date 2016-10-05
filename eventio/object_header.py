import struct
from .tools import read_from
import logging
log = logging.getLogger(__name__)

from functools import namedtuple
TypeInfo = namedtuple('TypeInfo', 'type version user extended')


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


LITTLE_ENDIAN_MARKER = 0xD41F8A37
BIG_ENDIAN_MARKER = struct.unpack("<I", struct.pack(">I", LITTLE_ENDIAN_MARKER))[0]
def parse_sync_bytes(int_value):
    ''' returns the endianness as given by the sync byte '''

    if int_value == LITTLE_ENDIAN_MARKER:
        return '<'
    elif int_value == BIG_ENDIAN_MARKER:
        return '>'
    else:
        raise ValueError(
            'Sync must be 0x{0:X} or 0x{1:X}. Got: {2:X}'.format(
                LITTLE_ENDIAN_MARKER, BIG_ENDIAN_MARKER, int_value)
        )

def ObjectHeader_from_file(cls, f, toplevel=True):
    '''create ObjectHeader from file.

    Depending on `toplevel` read 3 or 4 ints from the file
    and create an ObjectHeader from it.

    Keyword Arguments:
    f -- a file like object, supporting read and seek(also backwards)
    toplevel -- boolean (default: True)
    '''
    if toplevel is True:
        sync = read_from('<I', f)[0]
        endianness = parse_sync_bytes(sync)
    else:
        endianness = None

    _type, _id, length = read_from('<3I', f)

    _type = unpack_type(_type)
    only_sub_objects, length = unpack_length(length)

    if _type.extended:
        extended, = read_from('<I', f)
        length = extend_length(extended, length)

    _tell = f.tell()
    return cls(
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


ObjectHeader = namedtuple(
    'ObjectHeader',
    [
        'endianness', 'type', 'version', 'user', 'extended',
        'only_sub_objects',  'length', 'id', 'data_field_first_byte',
    ]
)

ObjectHeader.from_file = classmethod(ObjectHeader_from_file)