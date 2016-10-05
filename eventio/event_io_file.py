import struct
from .object_header import ObjectHeader
from io import BytesIO

class EventIOObject:
    ''' A generic EventIOObject

    It has a list of `headers` and a binary string `payload`.
    The payload might be loaded lazily on first access or already in memory.
    This is decided on construction time.
    '''
    def __init__(self, headers, file):
        self._file = file
        self.headers = headers

    def __getattr__(self, attr):
        if attr == "payload":
            self._file.seek(self.headers[-1].data_field_first_byte)
            self.payload = self._file.read(self.headers[-1].length)
        return self.payload

    def __repr__(self):
        return repr(self.headers)

def objects(file):
    return [o for o in yield_all_objects(file)]
    # file is not closed here, since the EventIOObjects, need to read from it
    # who closes this file? I don't know.

def yield_all_objects(f, previous_headers=None, toplevel=True, end_of_stream_pos=None):
    if previous_headers is None:
        previous_headers = []
    while True:
        try:
            header = ObjectHeader.from_file(f, toplevel)
            f.seek(header.data_field_first_byte)
            if not header.only_sub_objects:
                yield EventIOObject(headers=previous_headers + [header], file=f)
            else:
                for o in yield_all_objects(
                        f,
                        previous_headers=previous_headers + [header],
                        toplevel=False,
                        end_of_stream_pos=header.data_field_first_byte + header.length,
                    ):
                    yield o
            pos = f.seek(header.data_field_first_byte + header.length)
        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break

        if end_of_stream_pos and end_of_stream_pos <= pos:
            break
