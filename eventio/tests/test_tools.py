from io import BytesIO
import struct


def test_read_string():
    from eventio.tools import read_eventio_string
    s = b'Hello World'

    buffer = BytesIO()

    buffer.write(struct.pack('<h', len(s)))
    buffer.write(s)
    buffer.seek(0)

    assert read_eventio_string(buffer) == s
