import gzip
import tempfile
import pkg_resources
import os

testfile = pkg_resources.resource_filename(
    'eventio', os.path.join('resources', 'one_shower.dat')
)
testfile_gz = pkg_resources.resource_filename(
    'eventio', os.path.join('resources', 'one_shower.dat.gz')
)


def test_is_gzip():
    from eventio.file_types import is_gzip

    with tempfile.NamedTemporaryFile(suffix='.gz') as tmp:
        with gzip.open(tmp.name, 'w') as f:
            f.write(b'hello world ')

        assert is_gzip(tmp.name)

        with open(tmp.name, 'wb') as f:
            f.write(b'lkdlsandlnl3nlasndla')

        assert not is_gzip(tmp.name)


def test_is_eventio():
    from eventio.file_types import is_eventio

    assert is_eventio(testfile)
    assert is_eventio(testfile_gz)
