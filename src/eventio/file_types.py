import gzip
try:
    import zstandard as zstd
except ModuleNotFoundError:
    zstd = None

from .constants import (
    SYNC_MARKER_SIZE,
    SYNC_MARKER_LITTLE_ENDIAN,
    SYNC_MARKER_BIG_ENDIAN,
)

ZSTD_MARKER = b'\x28\xb5\x2f\xfd'
GZIP_MARKER = b'\x1f\x8b'


def _check_marker(path, marker):
    with open(path, 'rb') as f:
        marker_bytes = f.read(len(marker))

    if len(marker_bytes) < len(marker):
        return False

    return marker_bytes == marker

def is_gzip(path):
    '''Test if a file is gzipped by reading its first two bytes and compare
    to the gzip marker bytes.
    '''
    return _check_marker(path, GZIP_MARKER)


def is_zstd(path):
    '''Test if a file is compressed using zstd using its magic marker bytes
    '''
    return _check_marker(path, ZSTD_MARKER)


def is_eventio(path):
    '''
    Test if a file is a valid eventio file by checking if the sync marker is there.
    '''
    if is_gzip(path):
        with gzip.open(path, 'rb') as f:
            marker_bytes = f.read(SYNC_MARKER_SIZE)
    elif is_zstd(path):
        if zstd is None:
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
