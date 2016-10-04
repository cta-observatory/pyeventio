from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter
from collections import OrderedDict
import struct
from .tools import read_ints
import logging
log = logging.getLogger()

from functools import namedtuple
TypeInfo = namedtuple('TypeInfo', 'type version user extended')


SYNC_MARKER_INT_VALUE = -736130505

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


def parse_sync_bytes(sync):
    ''' returns the endianness as given by the sync byte '''

    int_value, = struct.unpack('<i', sync)
    if int_value == SYNC_MARKER_INT_VALUE:
        log.debug('Found Little Endian byte order')
        return '<'

    int_value, = struct.unpack('>i', sync)
    if int_value == SYNC_MARKER_INT_VALUE:
        log.debug('Found Big Endian byte order')
        return '>'

    raise ValueError(
        'Sync must be 0xD41F8A37 or 0x378A1FD4. Got: {}'.format(sync)
    )

class ObjectHeader(tuple):
    'ObjectHeader(endianness, type, version, user, extended, only_sub_objects, length, id, data_field_first_byte, level)'

    __slots__ = ()

    _fields = ('endianness', 'type', 'version', 'user', 'extended', 'only_sub_objects', 'length', 'id', 'data_field_first_byte', 'level')

    def __new__(_cls, f, toplevel=True):
        _start_point = f.tell()

        if toplevel is True:
            sync = f.read(4)
            try:
                endianness = parse_sync_bytes(sync)
            except ValueError:
                f.seek(_start_point)
                raise
            level = 0
        else:
            endianness = None
            level = None

        if endianness == '>':
            raise NotImplementedError('Big endian byte order is not supported by this reader')

        _type, _id, length = read_ints(3, f)

        _type = unpack_type(_type)
        only_sub_objects, length = unpack_length(length)

        if _type.extended:
            extended, = read_ints(1, f)
            length = extend_length(extended, length)

        _tell = f.tell()

        return _tuple.__new__(_cls, (
            endianness,
            _type.type,
            _type.version,
            _type.user,
            _type.extended,
            only_sub_objects,
            length,
            _id,
            _tell,
            level,
        ))



    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new ObjectHeader object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 10:
            raise TypeError('Expected 10 arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        'Return a new ObjectHeader object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('endianness', 'type', 'version', 'user', 'extended', 'only_sub_objects', 'length', 'id', 'data_field_first_byte', 'level'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '(endianness=%r, type=%r, version=%r, user=%r, extended=%r, only_sub_objects=%r, length=%r, id=%r, data_field_first_byte=%r, level=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    endianness = _property(_itemgetter(0), doc='Alias for field number 0')

    type = _property(_itemgetter(1), doc='Alias for field number 1')

    version = _property(_itemgetter(2), doc='Alias for field number 2')

    user = _property(_itemgetter(3), doc='Alias for field number 3')

    extended = _property(_itemgetter(4), doc='Alias for field number 4')

    only_sub_objects = _property(_itemgetter(5), doc='Alias for field number 5')

    length = _property(_itemgetter(6), doc='Alias for field number 6')

    id = _property(_itemgetter(7), doc='Alias for field number 7')

    data_field_first_byte = _property(_itemgetter(8), doc='Alias for field number 8')

    level = _property(_itemgetter(9), doc='Alias for field number 9')


