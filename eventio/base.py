import struct
import gzip
import logging

from .file_types import is_gzip, is_eventio, is_zstd
from .header import parse_header_bytes, get_bits_from_word
from . import constants
from .exceptions import WrongType

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
        self._next_header_pos = 0
        return self

    def __next__(self):
        self._filehandle.seek(self._next_header_pos)
        read_sync_marker(self)
        header = read_header(
            self,
            toplevel=True,
            offset=self._next_header_pos,
        )
        self._next_header_pos += header.total_size

        return KNOWN_OBJECTS.get(header.type, EventIOObject)(
            header,
            filehandle=self._filehandle,
        )

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


def check_size_or_raise(data, expected_length, zero_ok=True):
    if len(data) == 0:
        if zero_ok:
            raise StopIteration
        else:
            raise EOFError('File seems to be truncated')

    if len(data) < expected_length:
        raise EOFError('File seems to be truncated')


def read_sync_marker(byte_stream):
    '''
    Read the sync marker from the filehandle.
    Assumes position of `byte_stream` is at the beginning of a new toplevel header.

    Raises stop iteration if not enough data is available.
    Raises NotImplementedError if BigEndian sync marker is encountered
    '''
    sync = byte_stream.read(constants.SYNC_MARKER_SIZE)
    check_size_or_raise(sync, constants.SYNC_MARKER_SIZE, zero_ok=True)

    endianness = parse_sync_bytes(sync)

    if endianness == '>':
        raise NotImplementedError(
            'Big endian byte order is not supported by this reader'
        )


def read_header(byte_stream, offset, toplevel=False):
    '''Read the next header object from the file
    Assumes position of `byte_stream` is at the beginning of a new header.

    Raises stop iteration if not enough data is available.
    '''

    header_bytes = byte_stream.read(constants.OBJECT_HEADER_SIZE)
    check_size_or_raise(
        header_bytes,
        constants.OBJECT_HEADER_SIZE,
        zero_ok=False,
    )

    header = parse_header_bytes(header_bytes, toplevel=toplevel)

    if header.extended:
        extension_field = byte_stream.read(constants.EXTENSION_SIZE)
        check_size_or_raise(
            extension_field,
            constants.EXTENSION_SIZE,
            zero_ok=True
        )
        ext = parse_extension_field(extension_field)
        header.content_size += ext

    header.content_address = offset + header.header_size

    return header


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
        - a binary data blob
        - A list of other `EventIOObject`s

    If an `EventIOObject` is a pure list of other `EventIOObject`s,
    it can be iterated.
    Otherwise, parsing of the binary data has to be implented in a subclass
    or done "by hand" after reading the payload bytes.
    '''
    eventio_type = None

    def __init__(self, header, filehandle):
        if self.eventio_type is not None and header.type != self.eventio_type:
            raise WrongType(self.eventio_type, header.type)

        self._filehandle = filehandle
        self.header = header
        self.address = self.header.content_address
        self.size = self.header.content_size
        self.only_subobjects = self.header.only_subobjects
        self._next_header_pos = 0
        self._pos = 0

    def read(self, size=-1):
        '''Read bytes from the payload of this object.

        Parameters
        ----------
        size: int
            read `size` bytes from the payload of this object
            If size == -1 (default), read all remaining bytes.
        '''
        # read all remaining bytes.
        remaining = self.size - self._pos
        if size == -1 or size > remaining:
            size = remaining

        data = self._filehandle.read(size)
        self._pos += len(data)

        return data

    def __iter__(self):
        if not self.header.only_subobjects:
            raise ValueError(
                'Only EventIOObjects that contain just subobjects are iterable'
            )
        self._next_header_pos = 0
        return self

    def __next__(self):
        if not self.only_subobjects:
            raise ValueError(
                'Only EventIOObjects that contain just subobjects are iterable'
            )

        if self._next_header_pos >= self.size:
            raise StopIteration

        self.seek(self._next_header_pos)
        header = read_header(
            self,
            toplevel=False,
            offset=self.address + self._next_header_pos,
        )
        self._next_header_pos += header.total_size

        return KNOWN_OBJECTS.get(header.type, EventIOObject)(
            header, filehandle=self._filehandle
        )

    def seek(self, offset, whence=0):
        address = self.address
        if whence == 0:
            assert offset >= 0
            new_pos = self._filehandle.seek(address + offset, whence)
        elif whence == 1:
            new_pos = self._filehandle.seek(offset, whence)
        elif whence == 2:
            if offset > self.size:
                offset = self.size
            new_pos = self._filehandle.seek(address + self.size - offset, 0)
        else:
            raise ValueError(
                'invalid whence ({}, should be 0, 1 or 2)'.format(whence)
            )
        self._pos = new_pos - address
        return self._pos

    def tell(self):
        return self._pos

    def __repr__(self):
        return '{}[{}](size={}, only_subobjects={}, address={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.header.content_size,
            self.header.only_subobjects,
            self.header.content_address
        )

    def __str__(self):
        return '{}[{}]'.format(self.__class__.__name__, self.header.type)


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
