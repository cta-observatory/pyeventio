from .exceptions import WrongTypeException


class EventIOObject:
    eventio_type = None

    def __init__(self, eventio_file, header, first_byte):
        if header.type != self.eventio_type:
            raise WrongTypeException(self.eventio_type, header.type)

        self.eventio_file = eventio_file
        self.first_byte = first_byte
        self.header = header

    def __repr__(self):
        return '{}(first={}, length={})'.format(
            self.__class__.__name__,
            self.first_byte,
            self.header.length,
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
