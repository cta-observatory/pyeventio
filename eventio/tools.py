import struct
import numpy as np

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


def read_ints(n, f):
    ''' read n ints from file f '''
    return read_from('{:d}i'.format(n), f)


def read_from_without_position_change(fmt, f):
    ''' Read struct format and return to old cursor position '''
    position = f.tell()
    result = read_from(fmt, f)
    f.seek(position)
    return result


def get_scount(data):
    # this is mostly a verbatim copy from eventio.c lines 1082ff
    u = get_count(data)
    # u values of 0,1,2,3,4,... here correspond to signed values of
    #   0,-1,1,-2,2,... We have to test the least significant bit:
    if (u & 1) == 1:  # Negative number;
        return -(u >> 1) - 1
    else:
        return u >> 1


def get_count(data):
    '''this returns a python integer'''
    a = np.frombuffer(data, dtype='B', count=9).copy()
    b = np.zeros(8, dtype='B')

    # FIXME avoid this loop to make it faster.
    # find the most significant zero in a[0]
    for pos_of_msb_zero in range(8)[::-1]:  # pos_of_msb_zero goes from 7..0
        if ~a[0] & 1 << pos_of_msb_zero:
            break

    # mask away some leading ones in a[0]
    a[0] &= (1 << (pos_of_msb_zero + 1)) - 1

    # copy the interesting part from a into b and return a view
    b[pos_of_msb_zero:] = a[0:8 - pos_of_msb_zero]  # b has a length from 1 to 8

    # FIXME: I read all 9 bytes .. but I should only read as many as I need for the
    # int .. so I should seek back.
    return int(b.view('>u8')[0])
