# cython: language_level=3
import cython

cdef unsigned int OBJECT_HEADER_SIZE = 12
cdef unsigned int EXTENSION_SIZE = 4

cdef unsigned int TYPE_N_BITS = 16
cdef unsigned int TYPE_POS = 0

cdef unsigned int USER_N_BITS = 1
cdef unsigned int USER_POS = 16

cdef unsigned int EXTENDED_N_BITS = 1
cdef unsigned int EXTENDED_POS = 17

cdef unsigned int VERSION_N_BITS = 12
cdef unsigned int VERSION_POS = 20

cdef unsigned int ONLY_SUBOBJECTS_N_BITS = 1
cdef unsigned int ONLY_SUBOBJECTS_POS = 30

cdef unsigned int LENGTH_N_BITS = 30
cdef unsigned int LENGTH_POS = 0

cdef unsigned int EXTENSION_N_BITS = 12
cdef unsigned int EXTENSION_POS = 0

cdef class ObjectHeader:
    cdef public str endianness
    cdef readonly unsigned int type
    cdef readonly unsigned int version
    cdef readonly bint user
    cdef readonly bint extended
    cdef readonly bint only_subobjects
    cdef public unsigned long length
    cdef readonly unsigned long id
    cdef public unsigned long address

    def __repr__(self):
        return (
            'Header[{}]('.format(self.type)
            + 'endianness={}, '.format(self.endianness)
            + 'version={}, '.format(self.version)
            + 'id={}, '.format(self.id)
            + 'user={}, '.format(self.user)
            + 'extended={}, '.format(self.extended)
            + 'only_subobjects={}, '.format(self.only_subobjects)
            + 'length={}, '.format(self.length)
            + 'address={})'.format(self.address)
        )


cpdef bint bool_bit_from_pos(unsigned int uint32_word, unsigned int pos):
    '''parse a Python Boolean from a bit a position `pos` in an
    unsigned 32bit integer.
    '''
    return uint32_word & (1 << pos)


cpdef unsigned int get_bits_from_word(
    unsigned int uint32_word,
    unsigned int n_bits,
    unsigned int first,
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


cdef (unsigned int, unsigned int, bint, bint) parse_type_field(unsigned int word):
    '''parse TypeInfo
    '''
    type_ = get_bits_from_word(word, TYPE_N_BITS, TYPE_POS)
    user_bit = bool_bit_from_pos(word, USER_POS)
    extended = bool_bit_from_pos(word, EXTENDED_POS)
    version = get_bits_from_word(word, VERSION_N_BITS, VERSION_POS)
    return type_, version, user_bit, extended


@cython.boundscheck(False)
@cython.wraparound(False)
cdef unsigned long unpack_uint32(const unsigned char[:] data):
    return (
        (<unsigned long> data[0])
        + ((<unsigned long> data[1]) << 8)
        + ((<unsigned long> data[2]) << 16)
        + ((<unsigned long> data[3]) << 24)
    )


cpdef ObjectHeader parse_header_bytes(const unsigned char[:] header_bytes):
    cdef unsigned long type_int
    cdef unsigned long id_field
    cdef unsigned long length_field

    cdef unsigned long type_
    cdef bint user
    cdef bint extended
    cdef unsigned long version
    cdef bint only_subobjects
    cdef unsigned long length


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
    header.length = length

    return header
