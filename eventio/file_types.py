import gzip

from .constants import (
    SYNC_MARKER_SIZE,
    SYNC_MARKER_LITTLE_ENDIAN,
    SYNC_MARKER_BIG_ENDIAN,
)


def is_gzip(path):
    '''Test if a file is gzipped by reading its first two bytes and compare
    to the gzip marker bytes.
    '''
    with open(path, 'rb') as f:
        marker_bytes = f.read(2)

    return marker_bytes[0] == 0x1f and marker_bytes[1] == 0x8b


def is_eventio(path):
    '''
    Test if a file is a valid eventio file by checking if the sync marker is there.
    '''
    if is_gzip(path):
        with gzip.open(path, 'rb') as f:
            marker_bytes = f.read(SYNC_MARKER_SIZE)
    else:
        with open(path, 'rb') as f:
            marker_bytes = f.read(SYNC_MARKER_SIZE)

    little = marker_bytes == SYNC_MARKER_LITTLE_ENDIAN
    big = marker_bytes == SYNC_MARKER_BIG_ENDIAN

    return little or big
