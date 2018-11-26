import gzip


def is_gzip(path):
    '''Test if a file is gzipped by reading its first two bytes and compare
    to the gzip marker bytes.
    '''
    with open(path, 'rb') as f:
        marker_bytes = f.read(2)

    return marker_bytes[0] == 0x1f and marker_bytes[1] == 0x8b


def is_eventio(path):
    '''
    Test if a file is an eventio file by checking it's first two bytes
    '''
    if is_gzip(path):
        with gzip.open(path, 'rb') as f:
            marker_bytes = f.read(4)
    else:
        with open(path, 'rb') as f:
            marker_bytes = f.read(4)

    return marker_bytes == b'\xd4\x1f\x8a\x37' or marker_bytes == b'\x37\x8a\x1f\xd4'
