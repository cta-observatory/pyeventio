import struct
import numpy as np


def read_array(f, dtype, count):
    '''Read a numpy array with `dtype` of length `count` from file-like `f`'''
    dt = np.dtype(dtype)
    return np.frombuffer(f.read(count * dt.itemsize), count=count, dtype=dt)


def read_eventio_string(f):
    '''Read a string from eventio file or object f
    Eventio stores strings as a short
    '''
    length, = read_from('<h', f)
    return f.read(length)


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


def read_eventio_string(f):
    '''Read a string from eventio file or object f
    Eventio stores strings as a short
    '''
    length, = read_from('<h', f)
    return f.read(length)


def read_ints(n, f):
    ''' read n ints from file f '''
    return read_from('{:d}i'.format(n), f)


def read_from_without_position_change(fmt, f):
    ''' Read struct format and return to old cursor position '''
    position = f.tell()
    result = read_from(fmt, f)
    f.seek(position)
    return result


def read_time(f):
    '''Read a time as combination of seconds and nanoseconds'''
    sec, nano = read_from('<ii', f)
    return sec, nano


def read_utf8_like_signed_int(f):
    # this is mostly a verbatim copy from eventio.c lines 1082ff
    u = read_utf8_like_unsigned_int(f)
    # u values of 0,1,2,3,4,... here correspond to signed values of
    #   0,-1,1,-2,2,... We have to test the least significant bit:
    if (u & 1) == 1:  # Negative number;
        return -(u >> 1) - 1
    else:
        return u >> 1


# The dict below is used as a performance improvement in
# read_utf8_like_unsigned_int().
# position_of_most_significant_zero_in_byte
# stored in a dict for increased execution speed.
# (factor 8..10 faster, if building the dict can be ignored)
# This whole setup part here takes <1ms on my machine
POS_OF_MSB_ZERO_DICT = {}
for i in range(256):
    byte_ = bytes([i])

    # If there is no zero in the byte, we need to use -1
    # This is not one of the minus ones used for denoting an error or
    # an exceptional case, but we really need -1 here.
    POS_OF_MSB_ZERO_DICT[byte_] = -1
    # find the most significant zero in a[0]
    for pos_of_msb_zero in range(8)[::-1]:  # pos_of_msb_zero goes from 7..0
        if ~i & (1 << pos_of_msb_zero):
            POS_OF_MSB_ZERO_DICT[byte_] = pos_of_msb_zero
            break


def read_utf8_like_unsigned_int(f):
    '''this returns a python integer'''
    # this is a reimplementation from eventio.c lines 797ff
    _byte = f.read(1)
    start_byte = _byte[0]
    b = np.zeros(8, dtype='B')

    pos_of_msb_zero = POS_OF_MSB_ZERO_DICT[_byte]

    # mask away some leading ones in a[0]
    masked_start_byte = start_byte & ((1 << (pos_of_msb_zero + 1)) - 1)

    # copy the interesting part from a into b and return a view
    b[pos_of_msb_zero] = masked_start_byte
    b[pos_of_msb_zero + 1:] = np.frombuffer(
        f.read(7 - pos_of_msb_zero),
        dtype='B',
    )

    return int(b.view('>u8')[0])


def read_vector_of_uint32_scount_differential(f, count):
    return np.cumsum([read_utf8_like_signed_int(f) for _ in range(count)])


def read_vector_of_uint32_scount_differential_optimized(f, count):
    '''Stupid, pure python copy of eventio.c:1457'''
    output = np.empty(count, dtype='uint32')

    val = np.int32(0)
    for i in range(count):
        v0, = f.read(1)

        if (v0 & 0x80) == 0:  # one byte
            if (v0 & 1) == 0:  # positive
                val += v0 >> 1
            else:  # negative
                val -= (v0 >> 1) + 1
        elif (v0 & 0xc0) == 0x80:  # two bytes
            v1, = f.read(1)
            if (v1 & 1) == 0:  # positive
                val += ((v0 & 0x3f) << 7) | (v1 >> 1)
            else:  # negative
                val -= ((v0 & 0x3f) << 7) | ((v1 >> 1) + 1)
        elif (v0 & 0xe0) == 0xc0:  # three bytes
            v1, v2 = f.read(2)

            if (v2 & 1) == 0:
                val += (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | (v2 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | ((v2 >> 1) + 1)
                )
        elif (v0 & 0xf0) == 0xe0:  # four bytes
            v1, v2, v3 = f.read(3)
            if (v3 & 1) == 0:
                val += (
                    ((v0 & 0x0f) << 23)
                    | (v1 << 15)
                    | (v2 << 7)
                    | (v3 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x0f) << 23)
                    | (v1 << 15)
                    | (v2 << 7)
                    | ((v3 >> 1) + 1)
                )
        elif (v0 & 0xf8) == 0xf0:
            v1, v2, v3, v4 = f.read(4)
            # The format would allow bits 32 and 33 being set but we ignore this here. */
            if (v4 & 1) == 0:
                val += (
                    ((v0 & 0x07) << 31)
                    | (v1 << 23)
                    | (v2 << 15)
                    | (v3 << 7)
                    | (v4 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x07) << 31)
                    | (v1 << 23)
                    | (v2 << 15)
                    | (v3 << 7)
                    | ((v4 >> 1) + 1)
                )
        output[i] = val

    if count == 1:
        return val

    return output
