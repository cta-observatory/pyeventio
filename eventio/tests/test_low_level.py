import pkg_resources
import eventio
import struct
from os import path

one_shower = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

three_with_reuse = pkg_resources.resource_filename(
    'eventio', path.join('resources', '3_gammas_reuse_5.dat')
)

import eventio.object_header as oh
from pytest import raises
def test_parse_sync_bytes():
    assert '<' == oh.parse_sync_bytes(struct.pack('I', oh.LITTLE_ENDIAN_MARKER))
    assert '>' == oh.parse_sync_bytes(struct.pack('I', oh.BIG_ENDIAN_MARKER))
    with raises(ValueError):
        oh.parse_sync_bytes(struct.pack('I', 0))


from eventio.event_io_file import objects

def test_objects_have_headers_and_payload():

    for testfile in (one_shower, three_with_reuse):
        for o in objects(testfile):
            o.headers
            # payload is loaded on access only
            o.payload