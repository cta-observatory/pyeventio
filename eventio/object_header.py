import struct
from .tools import read_ints
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
def parse_sync_bytes(sync):
    ''' returns the endianness as given by the sync byte '''

    int_value = struct.unpack('<I', sync)[0]
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
    _start_point = f.tell()

    if toplevel is True:
        sync = f.read(4)
        try:
            endianness = parse_sync_bytes(sync)
        except ValueError:
            f.seek(_start_point)
            raise
        level = 0
    else:
        endianness = None
        level = None

    _type, _id, length = read_ints(3, f)

    _type = unpack_type(_type)
    only_sub_objects, length = unpack_length(length)

    if _type.extended:
        extended, = read_ints(1, f)
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
        level,
    )


ObjectHeader = namedtuple(
    'ObjectHeader',
    [
        'endianness', 'type', 'version', 'user', 'extended',
        'only_sub_objects',  'length', 'id', 'data_field_first_byte',
        'level'
    ]
)

ObjectHeader.from_file = classmethod(ObjectHeader_from_file)