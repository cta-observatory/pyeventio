import struct


def test_constants():
    from eventio.constants import (
        SYNC_MARKER_LITTLE_ENDIAN,
        SYNC_MARKER_BIG_ENDIAN,
        SYNC_MARKER_UINT_VALUE,
        SYNC_MARKER_INT_VALUE
    )

    assert struct.unpack('<L', SYNC_MARKER_LITTLE_ENDIAN)[0] == SYNC_MARKER_UINT_VALUE
    assert struct.unpack('<l', SYNC_MARKER_LITTLE_ENDIAN)[0] == SYNC_MARKER_INT_VALUE
    assert struct.unpack('>L', SYNC_MARKER_BIG_ENDIAN)[0] == SYNC_MARKER_UINT_VALUE
    assert struct.unpack('>l', SYNC_MARKER_BIG_ENDIAN)[0] == SYNC_MARKER_INT_VALUE
