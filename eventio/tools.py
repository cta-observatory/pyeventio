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


def read_double(f):
    ''' Read an 8 byte float from `f`'''
    return struct.unpack('<d', f.read(8))[0]


def read_array(f, dtype, count):
    '''Read a numpy array with `dtype` of length `count` from file-like `f`'''
    dt = np.dtype(dtype)
    if count == 0:
        return np.array((), dtype=dtype)
    return np.frombuffer(f.read(count * dt.itemsize), count=count, dtype=dt)


def read_string(f):
    '''Read a string from eventio file or object f.
    Eventio stores strings as a short giving the length
    of the string and the string itself.
    '''
    length = read_short(f)
    return f.read(length)


def read_var_string(f):
    '''Read a string from eventio file or object f.
    This string is similar to the one in `read_string` but uses
    the variable length integer instead of a short.
    '''
    length = read_unsigned_varint(f)
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


def read_time(f):
    '''Read a time as combination of seconds and nanoseconds'''
    sec, nano = read_from(f, '<ii')
    return sec, nano


def read_varint(f):
    u = read_unsigned_varint(f)
    # u values of 0,1,2,3,4,... here correspond to signed values of
    #   0,-1,1,-2,2,... We have to test the least significant bit:
    if (u & 1) == 1:  # Negative number;
        return -(u >> 1) - 1
    else:
        return u >> 1


def read_unsigned_varint(f):
    '''this returns a python integer'''
    var_int_bytes = bytearray(f.read(1))
    var_int_length = get_length_of_varint(var_int_bytes[0])
    if var_int_length > 1:
        var_int_bytes += f.read(var_int_length - 1)

    return parse_varint(var_int_bytes)
