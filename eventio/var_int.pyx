import numpy as np
cimport numpy as np

cpdef (unsigned long, unsigned int) unsigned_varint(const unsigned char[:] data, unsigned long offset=0):
    cdef unsigned int length
    cdef unsigned long value
    length = get_length_of_varint(data[0])
    value = parse_varint(data[offset:offset + length])
    return value, length


def varint(const unsigned char[:] data, unsigned long offset=0):
    cdef unsigned int length
    cdef unsigned long value
    value, length = unsigned_varint(data, offset)
    if (value & 1) == 1:  # Negative number;
        return -(value >> 1) - 1, length
    return value >> 1, length


cpdef unsigned int get_length_of_varint(const unsigned char first_byte):
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

cpdef unsigned long parse_varint(const unsigned char[:] var_int_bytes):
    length = var_int_bytes.shape[0]
    cdef unsigned long v[9]
    cdef long i  = 0
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


cpdef unsigned_varint_array(
    const unsigned char[:] data,
    unsigned long n_elements,
    unsigned long offset = 0,
):
    cdef np.ndarray[np.uint64_t, ndim=1] output = np.empty(n_elements, dtype='uint64')

    cdef int val
    cdef unsigned long i
    cdef unsigned long pos
    cdef unsigned long idx
    cdef unsigned char v0, v1, v2, v3, v4
    cdef unsigned long length
    pos = 0

    for i in range(n_elements):
        idx = pos + offset
        length = get_length_of_varint(data[idx])
        output[i] = parse_varint(data[idx:idx + length])
        pos += length

    return output, pos


def varint_array(
    const unsigned char[:] data,
    unsigned long n_elements,
    unsigned long offset = 0,
):
    cdef unsigned long bytes_read
    cdef np.ndarray[np.uint64_t, ndim=1] unsigned_output
    cdef np.ndarray[np.int64_t, ndim=1] output = np.empty(n_elements, dtype='int64')

    unsigned_output, bytes_read = unsigned_varint_array(data, n_elements, offset)

    cdef unsigned long one = 1;
    cdef unsigned long i

    for i in range(n_elements):
        if (unsigned_output[i] & one):
            output[i] = -(unsigned_output[i] >> one) - one
        else:
            output[i] = unsigned_output[i] >> one

    return output, bytes_read


cpdef unsigned_varint_arrays_differential(
    const unsigned char[:] data,
    unsigned long n_arrays,
    unsigned long n_elements,
    unsigned long offset = 0,
):
    cdef unsigned long pos = 0
    cdef unsigned long bytes_read = 0
    cdef unsigned long bytes_read_total = 0
    cdef unsigned long i
    cdef unsigned long j

    cdef np.ndarray[np.uint32_t, ndim=2] output = np.empty(
        (n_arrays, n_elements), dtype='uint32'
    )

    for i in range(n_arrays):

        output[i], bytes_read = unsigned_varint_array_differential(
            data, n_elements, offset=offset
        )
        offset += bytes_read
        bytes_read_total += bytes_read

    return output, bytes_read_total


cpdef unsigned_varint_array_differential(
    const unsigned char[:] data,
    unsigned long n_elements,
    unsigned long offset = 0,
):

    cdef np.ndarray[np.uint32_t, ndim=1] output = np.empty(n_elements, dtype='uint32')

    cdef int val = 0
    cdef unsigned long i
    cdef unsigned long pos = 0
    cdef unsigned char v0, v1, v2, v3, v4

    for i in range(n_elements):
        v0 = data[pos + offset]
        pos += 1

        if (v0 & 0x80) == 0:  # one byte
            if (v0 & 1) == 0:  # positive
                val += v0 >> 1
            else:  # negative
                val -= (v0 >> 1) + 1
        elif (v0 & 0xc0) == 0x80:  # two bytes
            v1 = data[pos + offset]
            pos += 1
            if (v1 & 1) == 0:  # positive
                val += ((v0 & 0x3f) << 7) | (v1 >> 1)
            else:  # negative
                val -= ((v0 & 0x3f) << 7) | ((v1 >> 1) + 1)
        elif (v0 & 0xe0) == 0xc0:  # three bytes
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            pos += 2

            if (v2 & 1) == 0:
                val += (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | (v2 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | ((v2 >> 1) + 1)
                )
        elif (v0 & 0xf0) == 0xe0:  # four bytes
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            v3 = data[pos + offset + 2]
            pos += 3
            if (v3 & 1) == 0:
                val += (
                    ((v0 & 0x0f) << 23)
                    | (v1 << 15)
                    | (v2 << 7)
                    | (v3 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x0f) << 23)
                    | (v1 << 15)
                    | (v2 << 7)
                    | ((v3 >> 1) + 1)
                )
        elif (v0 & 0xf8) == 0xf0:
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            v3 = data[pos + offset + 2]
            v4 = data[pos + offset + 3]
            pos += 4
            # The format would allow bits 32 and 33 being set but we ignore this here. */
            if (v4 & 1) == 0:
                val += (
                    ((v0 & 0x07) << 31)
                    | (v1 << 23)
                    | (v2 << 15)
                    | (v3 << 7)
                    | (v4 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x07) << 31)
                    | (v1 << 23)
                    | (v2 << 15)
                    | (v3 << 7)
                    | ((v4 >> 1) + 1)
                )
        output[i] = val

    return output, pos
