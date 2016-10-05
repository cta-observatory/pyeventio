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


from eventio.event_io_file import object_generator, object_list

def test_object_headers__equal__yield_objects():

    for testfile in (one_shower, three_with_reuse):
        lis = object_list(testfile)
        gen = object_generator(testfile)

        for i,o in enumerate(gen):
            assert o.headers == lis[i].headers
            # payload for the object in the list_of_objects gets only loaded now
            assert o.payload == lis[i].payload