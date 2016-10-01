import struct
import mmap
import logging

from .exceptions import WrongTypeException
from .objects import UnknownObject
from .header import ObjectHeader

log = logging.getLogger(__name__)


known_objects = {}


class EventIOFile:

    def __init__(self, path, debug=False):
        self.__file = open(path, 'rb')
        log.info('Opening new file {}'.format(path))
        self.path = path
        self.__mm = mmap.mmap(self.__file.fileno(), 0, prot=mmap.PROT_READ)

        self.__objects = []
        self._read_all_headers()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__mm.close()
        self.__file.close()

    def _read_all_headers(self):
        self.__mm.seek(0)
        while True:
            position = self.__mm.tell()
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
                self.__mm.seek(header.length, 1)
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
                self.__mm.seek(-header_length * 4, 1)
                raise WrongTypeException(expected_type, header.type)

        return header
