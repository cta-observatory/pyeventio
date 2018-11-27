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

def test_get_count():
    from eventio.tools import get_count
    testcases = [
        #(input, output, tell_after_done)
        (bytes([0b0111_1111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b0111_1111, 1),
        (bytes([0b0000_1111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b0000_1111, 1),

        (bytes([0b1011_1111, 0b1100_1100, 2, 3, 4, 5, 6, 7, 8]), 0b0011_1111_1100_1100, 2),

        (bytes([0b1101_1111, 0b1100_1100, 0b1010_1010, 3, 4, 5, 6, 7, 8]), 0b0001_1111_1100_1100_1010_1010, 3),

        (bytes([0b0000_0000, 1, 2, 3, 4, 5, 6, 7, 8]), 0, 1),
        (bytes([0b1111_1110, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]), 0x10203040506070, 8),
        (bytes([0b1111_1111, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]), 0x1020304050607080, 9),


    ]
    for data, expected_result, tell_after_done in testcases:
        stream = BytesIO(data)
        assert get_count(stream) == expected_result
        # make sure we do not seek too far
        assert stream.tell() == tell_after_done
