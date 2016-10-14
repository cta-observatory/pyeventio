import pkg_resources
import eventio
import struct
from os import path
from pytest import raises
import io

one_shower = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

three_with_reuse = pkg_resources.resource_filename(
    'eventio', path.join('resources', '3_gammas_reuse_5.dat')
)

def test_parse_sync_bytes():
    import eventio.file
    assert '<' == eventio.file.parse_sync_bytes(eventio.file.LITTLE_ENDIAN_MARKER)
    assert '>' == eventio.file.parse_sync_bytes(eventio.file.BIG_ENDIAN_MARKER)
    with raises(ValueError):
        eventio.file.parse_sync_bytes(0)

def test_payload_has_correct_size():
    from eventio.file import object_tree

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path, 'rb') as testfile:
            for obj in object_tree(testfile):
                if not obj._only_sub_objects:
                    data = obj.fetch_data()
                    assert len(data) == obj._length

def test_object_file_is_really_a_file():
    from eventio.file import object_tree

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path, 'rb') as testfile:
            for obj in object_tree(testfile):
                if not obj._only_sub_objects:
                    assert isinstance(obj._file, io.BufferedReader)
