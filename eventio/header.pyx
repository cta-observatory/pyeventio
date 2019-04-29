# cython: language_level=3
import cython
from libc.stdint cimport uint8_t, uint32_t, uint64_t


# cython's way to declare constants
# see https://cython.readthedocs.io/en/latest/src/userguide/language_basics.html#c-variable-and-type-definitions
cdef enum:
    OBJECT_HEADER_SIZE = 12
    EXTENSION_SIZE = 4
    SYNC_MARKER_SIZE = 4

    TYPE_N_BITS = 16
    TYPE_POS = 0

    USER_N_BITS = 1
    USER_POS = 16

    EXTENDED_N_BITS = 1
    EXTENDED_POS = 17

    VERSION_N_BITS = 12
    VERSION_POS = 20

    ONLY_SUBOBJECTS_N_BITS = 1
    ONLY_SUBOBJECTS_POS = 30

    LENGTH_N_BITS = 30
    LENGTH_POS = 0

    EXTENSION_N_BITS = 12
    EXTENSION_POS = 0



cdef class ObjectHeader:
    cdef readonly uint32_t id
    cdef readonly uint32_t type
    cdef readonly uint32_t version
    cdef readonly bint user
    cdef readonly bint extended
    cdef readonly bint only_subobjects
    cdef readonly uint8_t header_size
    cdef public uint64_t content_address
    cdef public uint64_t content_size

    @property
    def total_size(self):
        return self.content_size + self.header_size

    def __repr__(self):
        return (
            'Header[{}]('.format(self.type)
            + 'version={}, '.format(self.version)
            + 'id={}, '.format(self.id)
            + 'user={}, '.format(self.user)
            + 'extended={}, '.format(self.extended)
            + 'only_subobjects={}, '.format(self.only_subobjects)
            + 'header_size{}, '.format(self.header_size)
            + 'content_size={}, '.format(self.content_size)
            + 'content_address={})'.format(self.content_address)
        )


cpdef bint bool_bit_from_pos(uint32_t uint32_word, uint32_t pos):
    '''parse a Python Boolean from a bit a position `pos` in an
    unsigned 32bit integer.
    '''
    return uint32_word & (1 << pos)


cpdef uint32_t get_bits_from_word(
    uint32_t uint32_word,
    uint32_t n_bits,
    uint32_t first,
):
    '''return `n_bits` bits from the input word
    starting at first

    assume the input word was:
        MSB                                    LSB
        0000_0000__0000_0000__1010_1100__0000_0000

    and first=10 and n_bits=4

    the return value would be: 1011 (with leading zeros)
    '''
    return (uint32_word >> first) & ((1 << n_bits) - 1)


cdef (uint32_t, uint32_t, bint, bint) parse_type_field(uint32_t word):
    '''parse TypeInfo
    '''
    type_ = get_bits_from_word(word, TYPE_N_BITS, TYPE_POS)
    user_bit = bool_bit_from_pos(word, USER_POS)
    extended = bool_bit_from_pos(word, EXTENDED_POS)
    version = get_bits_from_word(word, VERSION_N_BITS, VERSION_POS)
    return type_, version, user_bit, extended


@cython.boundscheck(False)
@cython.wraparound(False)
cdef uint32_t unpack_uint32(const uint8_t[:] data):
    return (<uint32_t*> &data[0])[0]


cpdef ObjectHeader parse_header_bytes(const uint8_t[:] header_bytes, bint toplevel=0):
    cdef uint64_t type_int
    cdef uint64_t id_field
    cdef uint64_t length_field

    cdef uint64_t type_
    cdef bint user
    cdef bint extended
    cdef uint64_t version
    cdef bint only_subobjects
    cdef uint64_t length


    type_int = unpack_uint32(header_bytes[0:4])
    type_, version, user, extended = parse_type_field(type_int)
    id_field = unpack_uint32(header_bytes[4:8])

    length_field = unpack_uint32(header_bytes[8:12])

    only_subobjects = bool_bit_from_pos(length_field, ONLY_SUBOBJECTS_POS)
    length = get_bits_from_word(length_field, LENGTH_N_BITS, LENGTH_POS)

    header = ObjectHeader()
    header.type = type_
    header.user = user
    header.extended = extended
    header.version = version
    header.id = id_field
    header.only_subobjects = only_subobjects
    header.content_size = length
    header.header_size = OBJECT_HEADER_SIZE

    if toplevel:
        header.header_size += SYNC_MARKER_SIZE

    if header.extended:
        header.header_size += EXTENSION_SIZE

    return header
