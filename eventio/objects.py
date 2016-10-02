from .exceptions import WrongTypeException


class EventIOObject:
    eventio_type = None

    def __init__(self, eventio_file, header, first_byte):
        if header.type != self.eventio_type:
            raise WrongTypeException(self.eventio_type, header.type)

        self.eventio_file = eventio_file
        self.first_byte = first_byte
        self.header = header
        self.position = 0

    def __repr__(self):
        return '{}(first={}, length={})'.format(
            self.__class__.__name__,
            self.first_byte,
            self.header.length,
        )

    def read(self, size=-1):
        if size == -1 or size > self.header.length - self.position:
            size = self.header.length - self.position

        return self.eventio_file.read_from_position(
            first_byte=self.header.tell + self.position, size=size,
        )

    def seek(self, offset, whence=0):
        if whence == 0:
            assert offset >= 0
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = self.header.length + offset - 1
        else:
            raise ValueError('invalid whence ({}, should be 0, 1 or 2)'.format(whence))

    def tell(self):
        return self.position

    def read_from_data_field(self, first_byte, size):
        return self.eventio_file.read_from_position(
            first_byte=self.header.tell + first_byte, size=size,
        )


class UnknownObject(EventIOObject):
    def __init__(self, eventio_file, header, first_byte):
        self.eventio_type = header.type
        super().__init__(eventio_file, header, first_byte)

    def __repr__(self):
        return '{}[{}](first={}, length={})'.format(
            self.__class__.__name__,
            self.header.type,
            self.first_byte,
            self.header.length,
        )
