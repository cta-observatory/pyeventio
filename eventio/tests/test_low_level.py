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


from eventio.event_io_file import object_headers
def test_object_headers():
    list_of_headers = object_headers(one_shower)

from eventio.event_io_file import yield_objects
def test_yield_objects():
    for obj in yield_objects(one_shower):
        pass
