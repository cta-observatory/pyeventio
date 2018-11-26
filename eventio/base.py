import struct
from collections import namedtuple
import gzip
import logging
import warnings

from .file_types import is_gzip, is_eventio
from .bits import bool_bit_from_pos, get_bits_from_word
from . import constants

log = logging.getLogger(__name__)

known_objects = {}


class EventIOFile:

    def __init__(self, path):
        log.info('Opening new file {}'.format(path))
        self.path = path

        if not is_eventio(path):
            raise ValueError('File {} is not an eventio file'.format(path))

        if is_gzip(path):
            log.info('Found gzipped file')
            self._filehandle = gzip.open(path, mode='rb')
        else:
            log.info('Found uncompressed file')
            self._filehandle = open(path, mode='rb')

        self._next_header_pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        self._filehandle.seek(self._next_header_pos)
        header = self._read_next_header()
        self._next_header_pos = self._filehandle.tell() + header.length
        return EventIOObject(header, parent=self)

    def seek(self, position, whence=0):
        return self._filehandle.seek(position, whence)

    def tell(self):
        return self._filehandle.tell()

    def read(self, size=-1):
        return self._filehandle.read(size)

    def _read_next_header(self):
        '''Read the next header object from the file'''
        header_bytes = self._filehandle.read(constants.OBJECT_HEADER_SIZE)

        if len(header_bytes) == 0:
            raise StopIteration

        if len(header_bytes) < constants.OBJECT_HEADER_SIZE:
            log.warning('File seems to be truncated')
            warnings.warn('File seems to be truncated')
            raise StopIteration

        endianness = parse_sync_bytes(header_bytes[:4])

        if endianness == '>':
            raise NotImplementedError(
                'Big endian byte order is not supported by this reader'
            )

        type_version_field = parse_type_field(header_bytes[4:8])
        id_field = struct.unpack('<I', header_bytes[8:12])
        only_sub_objects, length = parse_length_field(header_bytes[12:16])

        if type_version_field.extended:
            extension_field = self._filehandle.read(constants.EXTENSION_SIZE)
            if len(extension_field) < constants.EXTENSION_SIZE:
                log.warning('File seems to be truncated')
                warnings.warn('File seems to be truncated')
                raise StopIteration
            length += parse_extension_field(extension_field)

        data_field_first_byte = self._filehandle.tell()

        return ObjectHeader(
            endianness,
            type_version_field.type,
            type_version_field.version,
            type_version_field.user,
            type_version_field.extended,
            only_sub_objects,
            length,
            id_field,
            data_field_first_byte,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self._filehandle.close()


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


class Object:

    def __init__(self, header, parent):


ObjectHeader = namedtuple(
    'ObjectHeader',
    [
        'endianness',
        'type',
        'version',
        'user',
        'extended',
        'only_sub_objects',
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

     - only_sub_objects: boolean
        This field tells us if the current object only consists of subobjects
        and does not contain any data on its own.
     - length: unsigend 30 bit unsigned integer
        The length of the data section of this object in bytes.
    '''
    word, = struct.unpack('<I', length_field)
    only_sub_objects = bool_bit_from_pos(word, constants.ONLY_SUBOBJECTS_POS)
    length = get_bits_from_word(word, constants.LENGTH_NUM_BITS, constants.LENGTH_POS)
    return only_sub_objects, length


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
