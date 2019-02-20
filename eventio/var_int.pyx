# cython: language_level=3
import cython
import numpy as np
cimport numpy as np

INT16 = np.int16
ctypedef np.int16_t INT16_t

UINT32 = np.uint32
ctypedef np.uint32_t UINT32_t

INT32 = np.int32
ctypedef np.int32_t INT32_t

UINT64 = np.uint64
ctypedef np.uint64_t UINT64_t

INT64 = np.int64
ctypedef np.int64_t INT64_t

cdef F32 = np.float32


@cython.wraparound(False)  # disable negative indexing
cpdef (UINT64_t, unsigned int) unsigned_varint(const unsigned char[:] data, unsigned long offset=0):
    cdef unsigned int length
    cdef unsigned long value
    length = get_length_of_varint(data[offset])
    value = parse_varint(data[offset:offset + length])
    return value, length


@cython.wraparound(False)  # disable negative indexing
cpdef (INT64_t, unsigned int) varint(const unsigned char[:] data, unsigned long offset=0):
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


@cython.boundscheck(False)
@cython.wraparound(False)  # disable negative indexing
cpdef UINT64_t parse_varint(const unsigned char[:] var_int_bytes):
    length = var_int_bytes.shape[0]
    cdef UINT64_t v[9]
    cdef int i  = 0
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


@cython.wraparound(False)  # disable negative indexing
cpdef unsigned_varint_array(
    const unsigned char[:] data,
    unsigned long n_elements,
    unsigned long offset = 0,
):
    cdef np.ndarray[UINT64_t, ndim=1] output = np.empty(n_elements, dtype=UINT64)

    cdef unsigned long i
    cdef unsigned long pos
    cdef unsigned long idx
    cdef unsigned long length
    pos = 0

    for i in range(n_elements):
        idx = pos + offset
        length = get_length_of_varint(data[idx])
        output[i] = parse_varint(data[idx:idx + length])
        pos += length

    return output, pos


@cython.wraparound(False)  # disable negative indexing
cpdef varint_array(
    const unsigned char[:] data,
    unsigned long n_elements,
    unsigned long offset = 0,
):
    cdef unsigned long bytes_read
    cdef np.ndarray[INT64_t, ndim=1] output = np.empty(n_elements, dtype=INT64)

    cdef INT64_t val
    cdef unsigned int length

    cdef int one = 1;
    cdef unsigned long i
    cdef unsigned long pos = offset

    for i in range(n_elements):
        length = get_length_of_varint(data[pos])
        val = parse_varint(data[pos:pos + length])
        pos += length

        if (val & one):
            output[i] = -(val >> one) - one
        else:
            output[i] = val >> one

    return output, pos - offset


@cython.wraparound(False)  # disable negative indexing
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
    cdef (unsigned long, unsigned long) shape = (n_arrays, n_elements)

    cdef np.ndarray[UINT32_t, ndim=2] output = np.zeros(shape, dtype=UINT32)
    cdef UINT32_t[:, :] output_view = output
    cdef UINT32_t[:] output_view_1d

    for i in range(n_arrays):

        output_view_1d = output_view[i]

        bytes_read = unsigned_varint_array_differential(
            data, output=output_view_1d, offset=offset
        )
        offset += bytes_read
        bytes_read_total += bytes_read

    return output, bytes_read_total


@cython.wraparound(False)  # disable negative indexing
cdef unsigned long unsigned_varint_array_differential(
    const unsigned char[:] data,
    UINT32_t[:] output,
    unsigned long offset = 0,
) except -1:

    cdef unsigned long n_elements = output.shape[0]
    cdef int val = 0
    cdef unsigned long i
    cdef unsigned long pos = 0
    cdef unsigned char v0, v1, v2, v3, v4

    for i in range(n_elements):
        v0 = data[pos + offset]
        pos += 1

        if (v0 & 0x80) == 0:  # one byte
            if (v0 & 0x01) == 0:  # positive
                val += v0 >> 1
            else:  # negative
                val -= (v0 >> 1) + 1
        elif (v0 & 0xc0) == 0x80:  # two bytes
            v1 = data[pos + offset]
            pos += 1
            if (v1 & 0x01) == 0:  # positive
                val += ((v0 & 0x3f) << 7) | (v1 >> 1)
            else:  # negative
                val -= (((v0 & 0x3f) << 7) | (v1 >> 1)) + 1
        elif (v0 & 0xe0) == 0xc0:  # three bytes
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            pos += 2

            if (v2 & 0x01) == 0:
                val += (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | (v2 >> 1)
                )
            else:
                val -= (
                    ((v0 & 0x1f) << 15)
                    | (v1 << 7)
                    | (v2 >> 1)
                ) + 1
        elif (v0 & 0xf0) == 0xe0:  # four bytes
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            v3 = data[pos + offset + 2]
            pos += 3
            if (v3 & 0x01) == 0:
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
                    | (v3 >> 1)
                ) + 1
        elif (v0 & 0xf8) == 0xf0:
            v1 = data[pos + offset + 0]
            v2 = data[pos + offset + 1]
            v3 = data[pos + offset + 2]
            v4 = data[pos + offset + 3]
            pos += 4
            # The format would allow bits 32 and 33 being set but we ignore this here. */
            if (v4 & 0x01) == 0:
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
                    | (v4 >> 1)
                ) + 1
        output[i] = val

    return pos



def simtel_pixel_timing_parse_list_type_2(
    const unsigned char[:] data,
    const INT16_t[:, :] pixel_list,
    int n_gains,
    int n_pixels,
    int n_types,
    bint with_sum,
    bint glob_only_selected,
    float granularity,
):
    cdef int start, stop, list_index
    cdef int i_pix, i_type
    cdef unsigned long pos = 0
    cdef unsigned int length = 0
    cdef INT16_t* short_ptr

    cdef np.ndarray[float, ndim=2] timval = np.full((n_pixels, n_types), np.nan, dtype=np.float32)
    cdef np.ndarray[INT32_t, ndim=2] pulse_sum_loc = np.zeros((n_gains, n_pixels), dtype=INT32)
    cdef np.ndarray[INT32_t, ndim=2] pulse_sum_glob = np.zeros((n_gains, n_pixels), dtype=INT32)

    for list_index in range(pixel_list.shape[0]):
        start = pixel_list[list_index][0]
        stop = pixel_list[list_index][1]

        for i_pix in range(start, stop + 1):
            for i_type in range(n_types):
                short_ptr = <INT16_t*> &data[pos]
                timval[i_pix, i_type] = granularity * short_ptr[0]
                pos += 2

            if with_sum:
                for i_gain in range(n_gains):
                    pulse_sum_loc[i_gain, i_pix], length = varint(data, offset=pos)
                    pos += length

                if glob_only_selected:
                    for i_gain in range(n_gains):
                        pulse_sum_glob[i_gain, i_pix], length = varint(data, offset=pos)
                        pos += length

    if with_sum and pixel_list.shape[0] > 0 and not glob_only_selected:
        for i_gain in range(n_gains):
            for i_pix in range(n_pixels):
                pulse_sum_glob[i_gain, i_pix], length = varint(data, offset=pos)
                pos += length

    return {
        'time': timval,
        'pulse_sum_glob': pulse_sum_glob,
        'pulse_sum_loc': pulse_sum_loc,
    }, pos


def parse_1208(
    const unsigned char[:] data,
    int n_pixels,
    int nonempty,
    int version,
    unsigned int flags
):

    cdef unsigned int length
    cdef INT32_t* int_ptr
    cdef INT16_t* short_ptr
    cdef float* float_ptr

    cdef np.ndarray[float, ndim=1] photoelectrons = np.zeros(n_pixels, dtype=F32)
    cdef np.ndarray[INT32_t, ndim=1] photon_counts = None
    cdef list time = [[] for _ in range(n_pixels)]
    cdef list amplitude

    if flags & 1:
        amplitude = [[] for _ in range(n_pixels)]
    else:
        amplitude = None

    cdef unsigned long pos = 0
    cdef int i, j

    for i in range(nonempty):
        if version > 2:
            pix_id, length = varint(data, offset=pos)
        else:
            short_ptr = <INT16_t*> &data[pos]
            pix_id = short_ptr[0]
            length = 2

        pos += length

        int_ptr = <INT32_t*> &data[pos]
        n_pe = int_ptr[0]
        pos += 4

        photoelectrons[pix_id] = n_pe
        for j in range(n_pe):
            float_ptr = <float*> &data[pos]
            time[pix_id].append(float_ptr[0])
            pos += 4

        if flags & 1:
            for j in range(n_pe):
                float_ptr = <float*> &data[pos]
                amplitude[pix_id].append(float_ptr[0])
                pos += 4

    if flags & 4:
        photon_counts = np.zeros(n_pixels, dtype=INT32)

        int_ptr = <INT32_t*> &data[pos]
        nonempty = int_ptr[0]
        pos += 4

        for i in range(nonempty):
            short_ptr = <INT16_t*> &data[pos]
            pix_id = short_ptr[0]
            pos += 2

            int_ptr = <INT32_t*> &data[pos]
            photon_counts[pix_id] = int_ptr[0]
            pos += 4

    return photoelectrons, time, amplitude, photon_counts


cpdef simtel_pixel_timing_parse_list_type_1(
    const unsigned char[:] data,
    const INT16_t[:] pixel_list,
    int n_gains,
    int n_pixels,
    int n_types,
    bint with_sum,
    bint glob_only_selected,
    float granularity,
):
    cdef int start, stop, list_index
    cdef long pixel_list_length = pixel_list.shape[0]
    cdef int i, i_gain, i_type, i_pix
    cdef unsigned int length = 0
    cdef INT16_t* short_ptr

    cdef np.ndarray[float, ndim=2] timval = np.full((n_pixels, n_types), np.nan, dtype=np.float32)
    cdef np.ndarray[INT32_t, ndim=2] pulse_sum_loc = np.zeros((n_gains, n_pixels), dtype=INT32)
    cdef np.ndarray[INT32_t, ndim=2] pulse_sum_glob = np.zeros((n_gains, n_pixels), dtype=INT32)


    cdef unsigned long pos = 0
    for i in range(pixel_list_length):
        i_pix = pixel_list[i]
        for i_type in range(n_types):
            short_ptr = <INT16_t*> &(data[pos])
            timval[i_pix, i_type] = granularity * short_ptr[0]
            pos += 2

        if with_sum:
            for i_gain in range(n_gains):
                pulse_sum_loc[i_gain, i_pix], length = varint(data, offset=pos)
                pos += length

            if glob_only_selected:
                for i_gain in range(n_gains):
                    pulse_sum_glob[i_gain, i_pix], length = varint(data, offset=pos)
                    pos += length

    if with_sum and len(pixel_list) > 0 and not glob_only_selected:
        for i_gain in range(n_gains):
            for i_pix in range(n_pixels):
                pulse_sum_glob[i_gain, i_pix], length = varint(
                    data, offset=pos,
                )
                pos += length

    return {
        'time': timval,
        'pulse_sum_glob': pulse_sum_glob,
        'pulse_sum_loc': pulse_sum_loc,
    }, pos



@cython.wraparound(False)  # disable negative indexing
cpdef read_sector_information_v2(
    const unsigned char[:] data,
    unsigned long n_pixels,
    unsigned long offset = 0,
):
    cdef unsigned long i
    cdef unsigned long length
    cdef int n

    cdef list sectors = []
    cdef np.ndarray[INT64_t, ndim=1] sector

    cdef unsigned long pos = offset
    for i in range(n_pixels):

        n, length = varint(data, offset=pos)
        pos += length

        sector, length = varint_array(data, n, offset=pos)
        pos += length
        sectors.append(sector)

    return sectors, pos - offset
