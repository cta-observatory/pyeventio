from io import BytesIO
import struct


def test_read_types():
    from eventio.tools import (
        read_short,
        read_unsigned_short,
        read_int,
        read_unsigned_int,
        read_float
    )

    b = BytesIO()
    b.write(struct.pack('h', -5))
    b.write(struct.pack('H', 300))
    b.write(struct.pack('i', -2**18))
    b.write(struct.pack('I', 2**18))
    b.write(struct.pack('f', 2.25))
    b.seek(0)

    assert read_short(b) == -5
    assert read_unsigned_short(b) == 300
    assert read_int(b) == -2**18
    assert read_unsigned_int(b) == 2**18
    assert read_float(b) == 2.25


def test_read_string():
    from eventio.tools import read_string
    s = b'Hello World'

    buffer = BytesIO()

    buffer.write(struct.pack('<h', len(s)))
    buffer.write(s)
    buffer.seek(0)

    assert read_string(buffer) == s


def test_read_unsigned_varint():
    from eventio.tools import read_unsigned_varint
    testcases = [
        # (input, output, tell_after_done)
        (bytes([0b01111111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b01111111, 1),
        (bytes([0b00001111, 1, 2, 3, 4, 5, 6, 7, 8]), 0b00001111, 1),

        (
            bytes([0b10111111, 0b11001100, 2, 3, 4, 5, 6, 7, 8]),
            0b0011111111001100,
            2
        ),

        (
            bytes([0b11011111, 0b11001100, 0b10101010, 3, 4, 5, 6, 7, 8]),
            0b000111111100110010101010,
            3
        ),

        (bytes([0b00000000, 1, 2, 3, 4, 5, 6, 7, 8]), 0, 1),
        (
            bytes([
                0b11111110, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]),
            0x10203040506070,
            8
        ),
        (
            bytes([
                0b11111111, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]),
            0x1020304050607080,
            9
        ),


    ]
    for data, expected_result, tell_after_done in testcases:
        f = BytesIO(data)
        assert read_unsigned_varint(f) == expected_result
        # make sure we do not seek too far
        assert f.tell() == tell_after_done
