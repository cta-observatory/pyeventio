import struct
from collections import namedtuple
import gzip
import logging
import warnings

from .file_types import is_gzip, is_eventio, is_zstd
from .bits import bool_bit_from_pos, get_bits_from_word
from . import constants
from .exceptions import WrongTypeException

try:
    import zstandard as zstd
    has_zstd = True
except ImportError:
    has_zstd = False

log = logging.getLogger(__name__)

KNOWN_OBJECTS = {}


class EventIOFile:

    def __init__(self, path):
        log.info('Opening new file {}'.format(path))
        self.path = path

        if not is_eventio(path):
            raise ValueError('File {} is not an eventio file'.format(path))

        if is_gzip(path):
            log.info('Found gzipped file')
            self._filehandle = gzip.open(path, mode='rb')
        elif is_zstd(path):
            log.info('Found zstd compressed file')
            if not has_zstd:
                raise IOError(
                    'You need to install the `zstandard module'
                    'to read zstd compressed file`'
                )
            cctx = zstd.ZstdDecompressor()
            self._filehandle = cctx.stream_reader(open(path, 'rb'))
        else:
            log.info('Found uncompressed file')
            self._filehandle = open(path, mode='rb')

        self._next_header_pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._filehandle.seek(self._next_header_pos)
        header = read_next_header(self)
        self._next_header_pos = self._filehandle.tell() + header.length
        return KNOWN_OBJECTS.get(header.type, EventIOObject)(header, parent=self)

    def seek(self, position, whence=0):
        return self._filehandle.seek(position, whence)

    def tell(self):
        return self._filehandle.tell()

    def read(self, size=-1):
        return self._filehandle.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._filehandle.close()


def check_size_or_stopiteration(data, expected_length, warn_zero=False):
    if len(data) == 0:
        if warn_zero:
            log.warning('File seems to be truncated')
            warnings.warn('File seems to be truncated')
        raise StopIteration

    if len(data) < expected_length:
        log.warning('File seems to be truncated')
        warnings.warn('File seems to be truncated')
        raise StopIteration


def read_next_header(eventio, toplevel=True):
    '''Read the next header object from the file
    Assumes position of `eventio` is at the beginning of a new header.

    Raises stop iteration if not enough data is available.
    '''
    if toplevel:
        sync = eventio.read(constants.SYNC_MARKER_SIZE)
        check_size_or_stopiteration(sync, constants.SYNC_MARKER_SIZE)
        endianness = parse_sync_bytes(sync)
    else:
        endianness = eventio.header.endianness

    if endianness == '>':
        raise NotImplementedError(
            'Big endian byte order is not supported by this reader'
        )

    header_bytes = eventio.read(constants.OBJECT_HEADER_SIZE)
    check_size_or_stopiteration(
        header_bytes, constants.OBJECT_HEADER_SIZE, warn_zero=toplevel
    )

    type_version_field = parse_type_field(header_bytes[0:4])
    id_field, = struct.unpack('<I', header_bytes[4:8])
    only_subobjects, length = parse_length_field(header_bytes[8:12])

    if type_version_field.extended:
        extension_field = eventio.read(constants.EXTENSION_SIZE)
        check_size_or_stopiteration(extension_field, constants.EXTENSION_SIZE, True)
        length += parse_extension_field(extension_field)

    data_field_first_byte = eventio.tell()

    return ObjectHeader(
        endianness,
        type_version_field.type,
        type_version_field.version,
        type_version_field.user,
        type_version_field.extended,
        only_subobjects,
        length,
        id_field,
        data_field_first_byte,
    )


def parse_sync_bytes(sync):
    ''' returns the endianness as given by the sync byte '''

    if sync == constants.SYNC_MARKER_LITTLE_ENDIAN:
        log.debug('Found Little Endian byte order')
        return '<'

    if sync == constants.SYNC_MARKER_BIG_ENDIAN:
        log.debug('Found Big Endian byte order')
        return '>'

    raise ValueError(
        'Sync must be 0xD41F8A37 or 0x378A1FD4. Got: {}'.format(sync)
    )


class EventIOObject:
    '''
    Base Class for eventio objects.
    Can be subclassed to implement different types of
    EventIO objects and how their data payload is parsed into
    python objects.

    EventIO objects can basically play two roles:
        - a binary or ascii data blob
        - A list of other `EventIOObject`s

    If an `EventIOObject` is a pure list of other `EventIOObject`s,
    it can be iterated.
    Otherwise, parsing of the binary data has to be implented in a subclass
    or done "by hand" after reading the payload bytes.
    '''
    eventio_type = None

    def __init__(self, header, parent):
        if self.eventio_type is not None and header.type != self.eventio_type:
            raise WrongTypeException(self.eventio_type, header.type)

        self.parent = parent
        self.header = header
        self._next_header_pos = 0

    def read(self, size=-1):
        '''Read bytes from the payload of this object.

        Parameters
        ----------
        size: int
            read `size` bytes from the payload of this object
            If size == -1 (default), read all remaining bytes.
        '''
        pos = self.tell()

        # read all remaining bytes.
        if size == -1 or size > self.header.length - pos:
            size = self.header.length - pos

        data = self.parent.read(size=size)

        return data

    def __iter__(self):
        if not self.header.only_subobjects:
            raise ValueError(
                'Only EventIOObjects that contain just subobjects are iterable'
            )
        return self

    def __next__(self):
        if not self.header.only_subobjects:
            raise ValueError(
                'Only EventIOObjects that contain just subobjects are iterable'
            )

        if self._next_header_pos >= self.header.length:
            raise StopIteration

        self.seek(self._next_header_pos)
        header = read_next_header(self, toplevel=False)
        self._next_header_pos = self.tell() + header.length
        return KNOWN_OBJECTS.get(header.type, EventIOObject)(header, parent=self)

    def seek(self, offset, whence=0):
        first = self.header.data_field_first_byte
        if whence == 0:
            assert offset >= 0
            self.parent.seek(first + offset, whence)
        elif whence == 1:
            self.parent.seek(offset, whence)
        elif whence == 2:
            if offset > self.header.length:
                offset = self.header.length
            self._position = self.parent.seek(first + self.header.length - offset, 0)
        else:
            raise ValueError(
                'invalid whence ({}, should be 0, 1 or 2)'.format(whence)
            )
        return self.tell()

    def tell(self):
        return self.parent.tell() - self.header.data_field_first_byte

    def __repr__(self):
        return '{}[{}](size={}, only_subobjects={}, first_byte={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.length,
            self.header.only_subobjects,
            self.header.data_field_first_byte
        )


ObjectHeader = namedtuple(
    'ObjectHeader',
    [
        'endianness',
        'type',
        'version',
        'user',
        'extended',
        'only_subobjects',
        'length',
        'id',
        'data_field_first_byte',
    ]
)

TypeInfo = namedtuple('TypeInfo', ['type', 'version', 'user', 'extended'])


def parse_type_field(type_field):
    '''parse TypeInfo

    TypeInfo is encoded in a 32bit word.
    '''
    word, = struct.unpack('<I', type_field)
    type_ = get_bits_from_word(word, constants.TYPE_NUM_BITS, constants.TYPE_POS)
    user_bit = bool_bit_from_pos(word, constants.USER_POS)
    extended = bool_bit_from_pos(word, constants.EXTENDED_POS)
    version = get_bits_from_word(word, constants.VERSION_NUM_BITS, constants.VERSION_POS)
    return TypeInfo(type_, version, user_bit, extended)


def parse_length_field(length_field):
    '''parse the "length field"

    The length field contains:

     - only_subobjects: boolean
        This field tells us if the current object only consists of subobjects
        and does not contain any data on its own.
     - length: unsigend 30 bit unsigned integer
        The length of the data section of this object in bytes.
    '''
    word, = struct.unpack('<I', length_field)
    only_subobjects = bool_bit_from_pos(word, constants.ONLY_SUBOBJECTS_POS)
    length = get_bits_from_word(word, constants.LENGTH_NUM_BITS, constants.LENGTH_POS)
    return only_subobjects, length


def parse_extension_field(extension_field):
    '''parse the so called "extension" field from `file`

    The length of an object can be so large, that it cannot be hold by the
    original `length` field which is 30bits long.
    In that case the most significant part of the length is stored in the
    so called "extension" field. The extension is 12bits long.

    So the total length of the object is:
        real_length = extension * 2^30 + original_lenth

    This function returns the extension *already multiplied with 2^30*
    so that the original length can simply be added to the result of this
    function in order to get the real length of the object.
    '''
    word, = struct.unpack('<I', extension_field)
    extension = get_bits_from_word(
        word, constants.EXTENSION_NUM_BITS, constants.EXTENSION_POS
    )

    # we push the length-extension so many bits to the left,
    # i.e. we multiply with such a high number, that we can simply
    # use the += operator  to combine the normal (small) length and this extension.
    extension <<= constants.LENGTH_NUM_BITS
    return extension
