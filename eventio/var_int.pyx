def get_length_of_varint(unsigned char first_byte):
    if (first_byte & 0x80) == 0:
        return 1
    if (first_byte & 0xc0) == 0x80:
        return 2
    if (first_byte & 0xe0) == 0xc0:
        return 3
    if (first_byte & 0xf0) == 0xe0:
        return 4
    if (first_byte & 0xf8) == 0xf0:
        return 5
    if (first_byte & 0xfc) == 0xf8:
        return 6
    if (first_byte & 0xfe) == 0xfc:
        return 7
    if (first_byte & 0xff) == 0xfe:
        return 8
    return 9


def parse_varint(unsigned char[:] var_int_bytes):
    length = var_int_bytes.shape[0]
    cdef unsigned long v[9]
    cdef i  = 0
    for i in range(length):
        v[i] = var_int_bytes[i]

    if length == 1:
        return v[0]

    if length == 2:
        return ((v[0] & 0x3f) <<8) | v[1]

    if length == 3:
        return (
            ((v[0] & 0x1f) << 16)
            | (v[1] << 8)
            | v[2]
        )

    if length == 4:
        return (
            ((v[0] & 0x0f) << 24)
            | (v[1] << 16)
            | (v[2] << 8)
            | v[3]
        )
    if length == 5:
        return (
            ((v[0] & 0x07) << 32)
            | (v[1] << 24)
            | (v[2] << 16)
            | (v[3] << 8)
            | v[4]
        )
    if length == 6:
        return (
            ((v[0] & 0x03) << 40)
            | (v[1] << 32)
            | (v[2] << 24)
            | (v[3] << 16)
            | (v[4] << 8)
            | v[5]
        )
    if length == 7:
        return (
            ((v[0] & 0x01) << 48)
            | (v[1] << 40)
            | (v[2] << 32)
            | (v[3] << 24)
            | (v[4] << 16)
            | (v[5] << 8)
            | v[6]
        )
    if length == 8:
        return (
            (v[1]<<48)
            | (v[2]<<40)
            | (v[3]<<32)
            | (v[4]<<24)
            | (v[5]<<16)
            | (v[6]<<8)
            | v[7]
        )

    return (
        (v[1]<<56)
        | (v[2]<<48)
        | (v[3]<<40)
        | (v[4]<<32)
        | (v[5]<<24)
        | (v[6]<<16)
        | (v[7]<<8)
        | v[8]
    )
