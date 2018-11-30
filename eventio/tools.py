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
