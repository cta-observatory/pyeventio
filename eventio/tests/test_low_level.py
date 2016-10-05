import pkg_resources
import eventio
import struct
from os import path
from pytest import raises

one_shower = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

three_with_reuse = pkg_resources.resource_filename(
    'eventio', path.join('resources', '3_gammas_reuse_5.dat')
)

def test_parse_sync_bytes():
    import eventio.object_header as oh
    assert '<' == oh.parse_sync_bytes(struct.pack('I', oh.LITTLE_ENDIAN_MARKER))
    assert '>' == oh.parse_sync_bytes(struct.pack('I', oh.BIG_ENDIAN_MARKER))
    with raises(ValueError):
        oh.parse_sync_bytes(struct.pack('I', 0))

def test_objects_have_headers_and_payload():
    from eventio.event_io_file import objects

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path) as testfile:
            for o in objects(testfile):
                o.headers
                # payload is loaded on access only
                o.payload