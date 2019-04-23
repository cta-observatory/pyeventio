# cython: language_level=3
import cython
from cpython cimport array
from libc.stdint cimport uint8_t, uint32_t, uint64_t, int16_t, int32_t
import numpy as np
cimport numpy as np

INT16 = np.int16

@cython.wraparound(False)  # disable negative indexing
cpdef read_sector_information_v1(
    const uint8_t[:] data,
    uint64_t n_pixels,
    uint64_t offset = 0,
):
    cdef uint64_t i
    cdef int32_t j, n
    cdef int16_t* short_ptr

    cdef list sectors = []
    cdef array.array sector

    cdef uint64_t pos = offset
    for i in range(n_pixels):

        short_ptr = <int16_t*> &data[pos]
        n = short_ptr[0]
        pos += 2

        sector = array.array('h')
        for j in range(n):
            short_ptr = <int16_t*> &data[pos]
            sector.append(short_ptr[0])
            pos += 2

        # FIXME:
        # according to a comment in the c-sources
        # there is might be an old bug here,
        # which is trailing zeros.
        # is an ascending list of numbes, so any zero
        # after the first position indicates the end of sector.
        #
        # DN: maybe this bug was fixed long ago,
        # so maybe we do not have to account for it here
        # I will check for it in the tests.
        sectors.append(sector)

    return sectors, pos - offset



@cython.wraparound(False)  # disable negative indexing
cpdef dict parse_mc_event(
    const uint8_t[:] data,
    uint32_t version
):

    cdef uint64_t pos = 0
    cdef float xcore, ycore, aweight
    cdef int32_t shower_num

    shower_num = (<int32_t*> &data[pos])[0]
    pos += 4
    xcore = (<float*> &data[pos])[0]
    pos += 4
    ycore = (<float*> &data[pos])[0]
    pos += 4

    if version >= 2:
        aweight = (<float*> &data[pos])[0]
    else:
        aweight = 1.0

    return {
        'shower_num': shower_num,
        'xcore': xcore,
        'ycore': ycore,
        'aweight': aweight
    }
