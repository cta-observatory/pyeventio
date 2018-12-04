# cython: language_level=3
from cython import view

cdef unsigned int OBJECT_HEADER_SIZE = 12
cdef unsigned int EXTENSION_SIZE = 4

cdef unsigned int TYPE_NUM_BITS = 16
cdef unsigned int TYPE_POS = 0

cdef unsigned int USER_NUM_BITS = 1
cdef unsigned int USER_POS = 16

cdef unsigned int EXTENDED_NUM_BITS = 1
cdef unsigned int EXTENDED_POS = 17

cdef unsigned int VERSION_NUM_BITS = 12
cdef unsigned int VERSION_POS = 20

cdef unsigned int ONLY_SUBOBJECTS_NUM_BITS = 1
cdef unsigned int ONLY_SUBOBJECTS_POS = 30

cdef unsigned int LENGTH_NUM_BITS = 30
cdef unsigned int LENGTH_POS = 0

cdef unsigned int EXTENSION_NUM_BITS = 12
cdef unsigned int EXTENSION_POS = 0


cpdef bint bool_bit_from_pos(unsigned int uint32_word, unsigned int pos):
    '''parse a Python Boolean from a bit a position `pos` in an
    unsigned 32bit integer.
    '''
    return uint32_word & (1 << pos)


cpdef unsigned int get_bits_from_word(
    unsigned int uint32_word,
    unsigned int num_bits,
    unsigned int first,
):
    '''return `num_bits` bits from the input word
    starting at first

    assume the input word was:
        MSB                                    LSB
        0000_0000__0000_0000__1010_1100__0000_0000

    and first=10 and num_bits=4

    the return value would be: 1011 (with leading zeros)
    '''
    return (uint32_word >> first) & ((1 << num_bits) - 1)


cdef (unsigned int, unsigned int, bint, bint) parse_type_field(unsigned int word):
    '''parse TypeInfo
    '''
    type_ = get_bits_from_word(word, TYPE_NUM_BITS, TYPE_POS)
    user_bit = bool_bit_from_pos(word, USER_POS)
    extended = bool_bit_from_pos(word, EXTENDED_POS)
    version = get_bits_from_word(word, VERSION_NUM_BITS, VERSION_POS)
    return type_, version, user_bit, extended


cdef unsigned long unpack_uint32(const unsigned char[:] data):
    return 5


cpdef parse_header_bytes(const unsigned char[:] header_bytes):
    cdef unsigned long type_int
    cdef unsigned long id_field
    cdef unsigned long* long_ptr

    long_ptr = <unsigned long*> &header_bytes[0]
    type_int = long_ptr[0]
    type_version_field = parse_type_field(type_int)
    long_ptr = <unsigned long*> &header_bytes[4]
    id_field = long_ptr[0]
    only_subobjects, length = parse_length_field(header_bytes[8:12])

    return type_int, type_version_field, id_field, only_subobjects, length


cdef (bint, unsigned long) parse_length_field(const unsigned char[:] length_field):
    '''parse the "length field"

    The length field contains:

     - only_subobjects: boolean
        This field tells us if the current object only consists of subobjects
        and does not contain any data on its own.
     - length: unsigend 30 bit unsigned integer
        The length of the data section of this object in bytes.
    '''
    word = unpack_uint32(length_field)
    only_subobjects = bool_bit_from_pos(word, ONLY_SUBOBJECTS_POS)
    length = get_bits_from_word(word, LENGTH_NUM_BITS, LENGTH_POS)
    return only_subobjects, length
