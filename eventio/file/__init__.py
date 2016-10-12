import struct
from functools import namedtuple

def object_tree(file, end=None, toplevel=True):
    if end is None:
        end = file.seek(0, 2)
        file.seek(0)

    pos = file.tell()
    tree = []
    while pos < end:
        header = ObjectHeader.from_file(file, toplevel)
        if header.only_sub_objects:
            data = object_tree(
                    file,
                    end=header.data_field_first_byte + header.length,
                    toplevel=False,
                )
        else:
            data = ObjectData(file=file, start_address=header.data_field_first_byte, length=header.length)
            file.seek(header.length, 1)
        tree.append((header, data))
        pos = file.tell()
    return tree


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

    type_version_field = read_type_field(f)
    id_field = read_from('<I', f)[0]
    only_sub_objects, length = read_length_field(f)
    if type_version_field.extended:
        length += read_extension(f)

    data_field_first_byte = f.tell()
    return cls(
        endianness,
        type_version_field.type,
        type_version_field.version,
        type_version_field.user,
        type_version_field.extended,
        only_sub_objects,
        length,
        id_field,
        data_field_first_byte,
    )

def read_from(fmt, f):
    '''
    read the struct fmt specification from file f
    Moves the current position.
    '''
    result = struct.unpack_from(
        fmt,
        f.read(struct.calcsize(fmt))
    )
    return result


ObjectHeader = namedtuple(
    'ObjectHeader',
    [
        'endianness', 'type', 'version', 'user', 'extended',
        'only_sub_objects',  'length', 'id', 'data_field_first_byte',
    ]
)

ObjectHeader.from_file = classmethod(ObjectHeader_from_file)

class ObjectData:
    def __init__(self, file, start_address, length):
        self._file = file
        self.start_address = start_address
        self.length = length

    def __getattr__(self, attr):
        if attr == "value":
            self._file.seek(self.start_address)
            self.value = self._file.read(self.length)
        return self.value

    def __repr__(self):
        return "{s.__class__.__name__}(addr={s.start_address}, len={s.length})".format(s=self)


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

TypeInfo = namedtuple('TypeInfo', 'type version user extended')

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
    # we push the length-extension some many bits to the left,
    # i.e. we multiply with such a high number, that we can simply
    # use the += operator further up in `ObjectHeader_from_file` to
    # combine the normal (small) length and this extension.
    extension <<= LENGTH_LEN
    return extension

