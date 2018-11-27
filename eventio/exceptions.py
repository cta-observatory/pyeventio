class WrongTypeException(Exception):
    '''
    This exception should be raised if an EventIO file contains
    an unxpected Object Type at the wanted position
    '''
    def __init__(self, expected, received):
        super().__init__(
            'Expected Object {} with type {} but received {} with type {}'.format(
                expected.__name__,
                expected.eventio_type,
                received.__class__.__name__,
                received.header.type
            )
        )


class WrongSizeException(Exception):
    '''
    This exception should be raised if an EventIO Object
    has the wrong size
    '''
    pass


def check_type(obj, expected):
    if not isinstance(obj, expected):
        raise WrongTypeException(expected, obj)
