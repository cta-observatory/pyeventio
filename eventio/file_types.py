import gzip
try:
    import zstandard as zstd
    has_zstd = True
except ImportError:
    has_zstd = False

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


def is_zstd(path):
    '''Test if a file is compressed using zstd using its magic marker bytes
    '''
    with open(path, 'rb') as f:
        marker_bytes = f.read(4)

    return marker_bytes == b'\x28\xb5\x2f\xfd'


def is_eventio(path):
    '''
    Test if a file is a valid eventio file by checking if the sync marker is there.
    '''
    if is_gzip(path):
        with gzip.open(path, 'rb') as f:
            marker_bytes = f.read(SYNC_MARKER_SIZE)
    elif is_zstd(path):
        if not has_zstd:
            raise IOError('You need the `zstandard` module to read zstd files')
        with open(path, 'rb') as f:
            cctx = zstd.ZstdDecompressor()
            with cctx.stream_reader(f) as stream:
                marker_bytes = stream.read(SYNC_MARKER_SIZE)
    else:
        with open(path, 'rb') as f:
            marker_bytes = f.read(SYNC_MARKER_SIZE)

    little = marker_bytes == SYNC_MARKER_LITTLE_ENDIAN
    big = marker_bytes == SYNC_MARKER_BIG_ENDIAN

    return little or big
