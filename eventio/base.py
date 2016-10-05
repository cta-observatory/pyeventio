import struct
from collections import namedtuple
import mmap
import gzip

import logging
import warnings
import io

from .tools import read_ints
from .exceptions import WrongTypeException
from .object_header import make_ObjectHeader

log = logging.getLogger(__name__)

known_objects = {}

class EventIOFile:

    def __init__(self, path):
        log.info('Opening new file {}'.format(path))
        self.path = path
        self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        if path.endswith('.gz'):
            log.info('Found gzipped file')
            self.__compfile = gzip.GzipFile(mode='r', fileobj=self.__mm)
            self.__filehandle = io.BufferedReader(self.__compfile)
        else:
            log.info('Found uncompressed file')
            self.__filehandle = self.__mm

        self.objects = read_all_headers(self, toplevel=True)
        log.info('File contains {} top level objects'.format(len(self.objects)))

    def __len__(self):
        return len(self.objects)

    def seek(self, position, whence=0):
        return self.__filehandle.seek(position, whence)

    def tell(self):
        return self.__filehandle.tell()

    def read(self, size=-1):
        return self.__filehandle.read(size)

    def read_from_position(self, first_byte, size):
        pos = self.__filehandle.tell()
        self.seek(first_byte)
        data = self.read(size)
        self.seek(pos)
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__mm.close()
        self.__file.close()

    def __getitem__(self, idx):
        return self.objects[idx]

    def __iter__(self):
        return iter(self.objects)

    def __repr__(self):
        r = '{}(path={}, objects=[\n'.format(self.__class__.__name__, self.path)

        if len(self.objects) <= 8:
            for o in self.objects:
                r += '  {}\n'.format(o)
        else:
            for o in self.objects[:4]:
                r += '  {}\n'.format(o)
            r += '\t...\n'
            for o in self.objects[-4:]:
                r += '  {}\n'.format(o)
        r += '])'
        return r


class EventIOObject:
    eventio_type = None

    def __init__(self, eventio_file, header, first_byte):
        if header.type != self.eventio_type:
            raise WrongTypeException(self.eventio_type, header.type)

        self.eventio_file = eventio_file
        self.first_byte = first_byte
        self.header = header
        self.position = 0

        self.objects = []

        if self.header.only_sub_objects:
            self.objects = read_all_headers(self, toplevel=False)

    def __getitem__(self, idx):
        return self.objects[idx]

    def parse_data_field(self):
        ''' Read the data in this field

        should return nice python objects, e.g. structured numpy arrays
        '''
        raise NotImplemented

    def __repr__(self):
        if len(self.objects) > 0:
            subitems = ', subitems={}'.format(len(self.objects))
        else:
            subitems = ''

        return '{}(first={}, length={}{})'.format(
            self.__class__.__name__,
            self.first_byte,
            self.header.length,
            subitems,
        )

    def read(self, size=-1):
        if size == -1 or size > self.header.length - self.position:
            size = self.header.length - self.position

        data = self.eventio_file.read_from_position(
            first_byte=self.header.data_field_first_byte + self.position, size=size,
        )

        self.position += size

        return data

    def read_from_position(self, first_byte, size):
        pos = self.tell()
        self.seek(first_byte)
        data = self.read(size)
        self.seek(pos)
        return data

    def seek(self, offset, whence=0):
        if whence == 0:
            assert offset >= 0
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = self.header.length + offset
        else:
            raise ValueError('invalid whence ({}, should be 0, 1 or 2)'.format(whence))
        return self.position

    def tell(self):
        return self.position


class UnknownObject(EventIOObject):
    def __init__(self, eventio_file, header, first_byte):
        self.eventio_type = header.type
        super().__init__(eventio_file, header, first_byte)

    def __repr__(self):
        first, *last = super().__repr__().split('(first')

        return '{}[{}](first'.format(
            self.__class__.__name__, self.eventio_type
        ) + ''.join(last)


def read_all_headers(eventio_file_or_object, toplevel=True):
    eventio_file_or_object.seek(0)
    objects = []
    while True:
        position = eventio_file_or_object.tell()
        try:
            header = make_ObjectHeader(
                eventio_file_or_object,
                toplevel,
            )
            log.debug(
                'Found header of type {} at byte {}'.format(header.type, position)
            )
            eventio_object = known_objects.get(header.type, UnknownObject)(
                eventio_file=eventio_file_or_object,
                header=header,
                first_byte=position,
            )
            objects.append(eventio_object)
            eventio_file_or_object.seek(header.length, 1)
        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break

    return objects
