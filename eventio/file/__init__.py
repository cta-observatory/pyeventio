import struct
from functools import namedtuple

class Object(list):
    def __init__(self, header=None, file=None, *args, **kwargs):
        super().__init__()
        if not header is None:
            self.type = header.type
            self.version = header.version
            self.id = header.id
            self.user = header.user

            self._only_sub_objects = header.only_sub_objects
            self._file = file
            self._length = header.length
            self._start_address = header.data_field_first_byte

    def fetch_data(self):
        if not self._only_sub_objects:
            self._file.seek(self._start_address)
            return self._file.read(self._length)
        else:
            return self

    def __repr__(self):
        header = ''
        if hasattr(self, 'type'):
            header = '{s.type},{s.version},{s.id}'.format(s=self)
        body = super().__repr__()[1:-1]
        return '<' + header + '|' + body + '>'

def object_tree(file, header=None, toplevel=True):
    if header is None:
        end = file.seek(0, 2)
        file.seek(0)
    else:
        end = header.data_field_first_byte + header.length

    pos = file.tell()
    tree = Object(header=header, file=file)
    while pos < end:
        header = ObjectHeader.from_file(file, toplevel)
        if header.only_sub_objects:
            tree.append(object_tree(
                    file,
                    header=header,
                    toplevel=False,
                ))
        else:
            file.seek(header.length, 1)
            tree.append(Object(header=header, file=file))
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

