class WrongTypeException(Exception):
    '''
    This exception should be raised if an EventIO file contains
    an unxpected Object Type at the wanted position
    '''
    def __init__(self, expected, received):
        super().__init__('Expected Type: {} but received {}'.format(
            expected, received
        ))


class WrongSizeException(Exception):
    '''
    This exception should be raised if an EventIO Object
    has the wrong size
    '''
    pass
