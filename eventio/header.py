from __future__ import absolute_import
from .tools import read_ints
from collections import namedtuple

TypeInfo = namedtuple("TypeInfo", "type version user extended")


def unpack_type(_type):
    t = _type & 0xffff
    version = (_type & 0xfff00000) >> 20
    user_bit = bool(_type & (1 << 16))
    extended = bool(_type & (1 << 17))
    return TypeInfo(t, version, user_bit, extended)


def unpack_length(length):
    only_sub_objects = bool(length & 1 << 30)
    # bit 31 of length is reserved
    length &= 0x3fffffff
    return only_sub_objects, length


def extend_length(extended, length):
    extended &= 0xfff
    length = length & extended << 12
    return length


def is_sync(i):
    sync = -736130505
    return i == sync


def read_header(f, top_level):
    _start_point = f.tell()

    if top_level:
        sync, _type, _id, length = read_ints(4, f)
    else:
        _type, _id, length = read_ints(3, f)

    _type = unpack_type(_type)
    only_sub_objects, length = unpack_length(length)

    if _type.extended:
        extended, = read_ints(1, f)
        length = extend_length(extended, length)

    if top_level and not is_sync(sync):
        f.seek(_start_point)
        raise ValueError("Header sync value 0xD41F8A37 not found")
    _tell = f.tell()
    return_value = (
        is_sync(sync) if top_level else True,
        _type.type,
        _type.version,
        _type.user,
        _type.extended,
        only_sub_objects,
        length,
        _id,
        _tell)

    return return_value


HeaderBase = namedtuple(
    "HeaderBase",
    "is_sync type version user extended only_sub_objects length id tell"
)


class Header(HeaderBase):
    def __new__(cls, f, top_level=True):
        self = super(Header, cls).__new__(cls, *read_header(f, top_level))
        return self
