# cython: language_level=3

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
