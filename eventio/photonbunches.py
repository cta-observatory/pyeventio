from __future__ import absolute_import
from collections import namedtuple

import numpy as np

from .tools import unpack_from, WrongTypeException, read_ints
from .header import unpack_type, unpack_length, extend_length


__all__ = [
    'PhotonBunchHeader',
]


PhotonBunchHeaderBase = namedtuple(
    'PhotonBunchHeaderBase',
    ' type version user extended only_sub_objects length id tell '
    ' array tel photons n_bunches is_compact '
)


def read_photon_bunch_header(f):

    _type, _id, length = read_ints(3, f)
    _type = unpack_type(_type)
    only_sub_objects, length = unpack_length(length)

    if _type.extended:
        extended, = read_ints(1, f)
        length = extend_length(extended, length)

    if not _type.type == 1205:
        header_length = 3 if not _type.extended else 4
        f.seek(header_length * -4, 1)
        raise WrongTypeException(
            'Wrong subhead type. Expected 1205, got:'+str(_type.type)
        )

    array, tel, photons, n_bunches = unpack_from('hhfi', f)
    length -= 12

    _tell = f.tell()
    return(
        _type.type,
        _type.version,
        _type.user,
        _type.extended,
        only_sub_objects,
        length,
        _id,
        _tell,
        array,
        tel,
        photons,
        n_bunches,
        bool(_type.version/1000 == 1),
    )


class PhotonBunchHeader(PhotonBunchHeaderBase):
    def __new__(cls, f):
        self = super(PhotonBunchHeader, cls).__new__(cls, *read_photon_bunch_header(f))
        return self


class PhotonBundle(object):
    def __init__(self, f):
        self.header = PhotonBunchHeader(f)
        self.bunches = read_bunches(f, self.header.n_bunches, self.header.is_compact)


def photon_bunches(f, headers_only):
    while True:
        try:
            pbh = PhotonBunchHeader(f)
            if headers_only:
                f.seek(pbh.length, 1)
                yield pbh
            else:
                bunches = read_bunches(f, pbh.n_bunches, pbh.is_compact)
                yield (pbh, bunches)
        except WrongTypeException:
            break


def read_bunches(f, n_bunches, compact):
    bunches = np.zeros(n_bunches, dtype=[
        ('x', 'f4'),
        ('y', 'f4'),
        ('cx', 'f4'),
        ('cy', 'f4'),
        ('time', 'f4'),
        ('zem', 'f4'),
        ('photons', 'f4'),
        ('lambda', 'f4'),
        ])

    if compact:
        element_type, size_in_bytes = np.int16, 2
    else:
        element_type, size_in_bytes = np.float32, 4

    block = np.frombuffer(
        f.read(n_bunches*8*size_in_bytes),
        dtype=element_type,
        count=n_bunches*8)
    block = block.reshape(n_bunches, 8)

    for i, n in enumerate(bunches.dtype.names):
        bunches[n] = block[:, i]

    if compact:
        bunches['x'] *= 0.1  # now in cm
        bunches['y'] *= 0.1  # now in cm

        # don't know the units
        bunches['cx'] /= 30000
        bunches['cy'] /= 30000
        #   bernloehr clips in his implementation of the reader.
        #   I am not sure I really want that.
        # bunches['cx'] = bunches['cx'].clip(a_min=-1., a_max=1.)
        # bunches['cy'] = bunches['cy'].clip(a_min=-1., a_max=1.)

        bunches['time'] *= 0.1  # in nanoseconds since first interaction.
        bunches['zem'] = np.power(10., bunches['zem']*0.001)
        bunches['photons'] *= 0.01
        # bunches['lambda']  # nothing needs to be done with lambda

    return bunches
