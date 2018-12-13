import gzip
import tempfile
import pytest

testfile = 'tests/resources/one_shower.dat'
testfile_gz = 'tests/resources/one_shower.dat.gz'
testfile_zstd = 'tests/resources/run102_gamma_za20deg_azm0deg-paranal-sst.corsika.zst'


def test_is_gzip():
    from eventio.file_types import is_gzip

    with tempfile.NamedTemporaryFile(suffix='.gz') as tmp:
        with gzip.open(tmp.name, 'w') as f:
            f.write(b'hello world ')

        assert is_gzip(tmp.name)

        with open(tmp.name, 'wb') as f:
            f.write(b'lkdlsandlnl3nlasndla')

        assert not is_gzip(tmp.name)


def test_is_zstd():
    from eventio.file_types import is_zstd
    assert is_zstd(testfile_zstd)

    with tempfile.NamedTemporaryFile(suffix='.zstd') as tmp:
        with open(tmp.name, 'wb') as f:
            f.write(b'lkdlsandlnl3nlasndla')

        assert not is_zstd(tmp.name)


def test_is_eventio():
    from eventio.file_types import is_eventio

    assert is_eventio(testfile)
    assert is_eventio(testfile_gz)


def test_is_eventio_zstd():
    from eventio.file_types import is_eventio

    pytest.importorskip('zstandard')
    assert is_eventio(testfile_zstd)
