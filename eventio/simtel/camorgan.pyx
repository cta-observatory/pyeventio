import numpy as np
cimport numpy as np


cpdef read_sector_information(
    const unsigned char[:] data,
    unsigned long n_pixels,
    unsigned long offset = 0,
):
    cdef unsigned long pos = 0
    cdef unsigned long bytes_read_total = 0
    cdef unsigned long i
    cdef list sectors = []


    for i in range(n_pixels):
        n = np.frombuffer(data, dtype='i2', count=1, offset=pos + offset)[0]
        pos += 2
        sector = np.frombuffer(data, dtype='i2', count=n, offset=offset + pos)
        pos += 2 * n

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

    return sectors, bytes_read_total

