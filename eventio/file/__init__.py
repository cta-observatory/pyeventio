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
        length &= read_extension(f)

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

def read_type_field(f):
    uint32_word = read_from('<I', f)[0]

    t = uint32_word & 0xffff
    version = (uint32_word & (0xfff << 20)) >> 20
    user_bit = bool(uint32_word & (1 << 16))
    extended = bool(uint32_word & (1 << 17))
    return TypeInfo(t, version, user_bit, extended)

def read_length_field(f):
    uint32_word = read_from('<I', f)[0]

    only_sub_objects = bool(uint32_word & 1 << 30)
    # bit 31 of uint32_word is reserved
    uint32_word &= 0x3fffffff
    return only_sub_objects, uint32_word

def read_extension(f):
    return (read_from('<I', f)[0] & 0xfff) << 30
