import struct
import mmap
import logging
import gzip
import warnings

from .exceptions import WrongTypeException
from .objects import UnknownObject
from .header import ObjectHeader
from .iact import iact_objects

log = logging.getLogger(__name__)


known_objects = {}
known_objects.update(iact_objects)


class EventIOFile:

    def __init__(self, path, debug=False):
        log.info('Opening new file {}'.format(path))
        self.path = path
        if path.endswith('.gz'):
            self.__file = gzip.open(path, 'rb')
        else:
            self.__file = open(path, 'rb')
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        self.__objects = []
        self._read_all_headers()

    def __repr__(self):
        r = '{}(path={}, objects=[\n'.format(self.__class__.__name__, self.path)

        if len(self.__objects) <= 8:
            for o in self.__objects:
                r += '  {}\n'.format(o)
        else:
            for o in self.__objects[:4]:
                r += '  {}\n'.format(o)
            r += '\t...\n'
            for o in self.__objects[-4:]:
                r += '  {}\n'.format(o)
        r += '])'
        return r

    def __len__(self):
        return len(self.__objects)

    def seek(self, position, whence=0):
        self.__mm.seek(position, whence)

    def tell(self):
        return self.__mm.tell()

    def read(self, size=-1):
        return self.__mm.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__mm.close()
        self.__file.close()

    def _read_all_headers(self):
        self.seek(0)
        while True:
            position = self.tell()
            try:
                header = self.__read_header()
                log.debug(
                    'Found header of type {} at byte {}'.format(header.type, position)
                )
                eventio_object = known_objects.get(header.type, UnknownObject)(
                    eventio_file=self,
                    header=header,
                    first_byte=position,
                )
                self.__objects.append(eventio_object)
                try:
                    self.seek(header.length, 1)
                except ValueError:
                    warnings.warn('File seems to be truncated')
                    break
            except struct.error:
                break

    def __getitem__(self, idx):
        return self.__objects[idx]

    def __iter__(self):
        return iter(self.__objects)

    def __read_header(self, expected_type=None):
        header = ObjectHeader(self.__mm)
        if expected_type is not None:
            if header.type != expected_type:
                header_length = 4 if not header.extended else 5
                self.seek(-header_length * 4, 1)
                raise WrongTypeException(expected_type, header.type)

        return header
