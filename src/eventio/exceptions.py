class WrongType(Exception):
    '''
    This exception should be raised if an EventIO file contains
    an unxpected Object Type at the wanted position
    '''
    def __init__(self, expected, received):
        if isinstance(expected, tuple):

            super().__init__(
                'Expected one of {}, but received {} with type {}'.format(
                    ['{}[{}]'.format(e.__name__, e.eventio_type) for e in expected],
                    received.__class__.__name__,
                    received.header.type
                )
            )

        else:
            super().__init__(
                'Expected Object {} with type {} but received {} with type {}'.format(
                    expected.__name__,
                    expected.eventio_type,
                    received.__class__.__name__,
                    received.header.type
                )
            )


class WrongSize(Exception):
    '''
    This exception should be raised if an EventIO Object
    has the wrong size
    '''
    pass


def check_type(obj, expected):
    if not isinstance(obj, expected):
        raise WrongType(expected, obj)
