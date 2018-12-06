import struct
import numpy as np
from .var_int import get_length_of_varint, parse_varint


def read_short(f):
    ''' Read a signed 2 byte integer from `f`'''
    return struct.unpack('<h', f.read(2))[0]


def read_unsigned_short(f):
    ''' Read an unsigned 2 byte integer from `f`'''
    return struct.unpack('<H', f.read(2))[0]


def read_int(f):
    ''' Read a signed 4 byte integer from `f`'''
    return struct.unpack('<i', f.read(4))[0]


def read_unsigned_int(f):
    ''' Read an signed 4 byte integer from `f`'''
    return struct.unpack('<I', f.read(4))[0]


def read_float(f):
    ''' Read a 4 byte float from `f`'''
    return struct.unpack('<f', f.read(4))[0]


def read_array(f, dtype, count):
    '''Read a numpy array with `dtype` of length `count` from file-like `f`'''
    dt = np.dtype(dtype)
    if count == 0:
        return np.array((), dtype=dtype)
    return np.frombuffer(f.read(count * dt.itemsize), count=count, dtype=dt)


def read_eventio_string(f):
    '''Read a string from eventio file or object f.
    Eventio stores strings as a short giving the length
    of the string and the string itself.
    '''
    length = read_short(f)
    return f.read(length)


def read_from(f, fmt):
    '''
    read the struct fmt specification from file f
    Moves the current position.
    '''
    result = struct.unpack_from(
        fmt,
        f.read(struct.calcsize(fmt))
    )
    return result


def read_ints(f, n_ints):
    ''' read n ints from file f '''
    return read_from(f, '{:d}i'.format(n_ints))


def read_from_without_position_change(f, fmt):
    ''' Read struct format and return to old cursor position '''
    position = f.tell()
    result = read_from(f, fmt)
    f.seek(position)
    return result


def read_time(f):
    '''Read a time as combination of seconds and nanoseconds'''
    sec, nano = read_from(f, '<ii')
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


def read_utf8_like_unsigned_int(f):
    '''this returns a python integer'''
    # this is a reimplementation from eventio.c lines 797ff
    var_int_bytes = bytearray(f.read(1))
    var_int_length = get_length_of_varint(var_int_bytes[0])
    if var_int_length - 1 > 0:
        var_int_bytes.extend(f.read(var_int_length - 1))

    return parse_varint(var_int_bytes)


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
