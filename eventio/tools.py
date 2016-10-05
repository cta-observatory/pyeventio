import struct


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

