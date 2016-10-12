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

def test_objects_have_headers_and_payload():
    from eventio.file import object_tree

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path, 'rb') as testfile:
            for header, data in object_tree(testfile):
                # data can be list or ObjectData instance.
                # lists have no `value` member, so for the moment I just try
                try:
                    data.value # fetching data from disk lazily.
                except AttributeError:
                    pass

def test_payload_has_correct_size():
    from eventio.file import object_tree

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path, 'rb') as testfile:
            for header, data in object_tree(testfile):
                try:
                    value = data.value
                except AttributeError:
                    pass
                else:
                    assert len(value) == header.length

def test_object_file_is_really_a_file():
    from eventio.file import object_tree

    for testfile_path in (one_shower, three_with_reuse):
        with open(testfile_path, 'rb') as testfile:
            for header, data in object_tree(testfile):
                try:
                    assert isinstance(data._file, io.BufferedReader)
                except AttributeError:
                    pass
