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
        #(input, output)
        (bytes([0b0111_1111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b0111_1111),
        (bytes([0b0000_1111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b0000_1111),

        (bytes([0b1011_1111, 0b1100_1100, 2, 3, 4, 5, 6, 7, 8]), 0b0011_1111_1100_1100),

        (bytes([0b1101_1111, 0b1100_1100, 0b1010_1010, 3, 4, 5, 6, 7, 8]), 0b0001_1111_1100_1100_1010_1010),
    ]
    for data, expected_result in testcases:
        assert get_count(BytesIO(data)) == expected_result

