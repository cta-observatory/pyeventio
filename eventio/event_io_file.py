import struct
from .object_header import ObjectHeader
from io import BytesIO

class EventIOObject:
    ''' A generic EventIOObject

    It has a list of `headers` and a binary string `payload`.
    The payload might be loaded lazily on first access or already in memory.
    This is decided on construction time.
    '''
    def __init__(self, headers, payload=None, file=None):
        if file is not None:
            self._file = file
        elif payload is not None:
            self._file = None
            self.payload = payload
        else:
            raise Exception('EventIOObject must have either file or payload')
        
        self.headers = headers

    def __getattr__(self, attr):
        if attr == "payload":
            if self._file.closed:
                self._file = open(self._file.name, 'rb')
            start_address = sum(h.data_field_first_byte for h in self.headers)
            self._file.seek(start_address)
            self.payload = self._file.read(self.headers[-1].length)
        return self.payload

    def __repr__(self):
        return repr(self.headers)

def object_generator(path):
    with open(path, 'rb') as f:
        for o in yield_all_objects(f, read_payload=True):
            yield o

def object_list(path):
    f = open(path, 'rb')
    return [o for o in yield_all_objects(f, read_payload=False)]
    # file is not closed here, since the EventIOObjects, need to read from it
    # who closes this file? I don't know.

def yield_all_objects(f, previous_headers=None, toplevel=True, read_payload=True):
    if previous_headers is None:
        previous_headers = []
    while True:
        try:
            header = ObjectHeader.from_file(f, toplevel)
            payload = f.read(header.length)
            if not header.only_sub_objects:
                if read_payload:
                    yield EventIOObject(headers=previous_headers + [header], payload=payload)
                else:
                    yield EventIOObject(headers=previous_headers + [header], file=f)
            else:
                for o in yield_all_objects(BytesIO(payload), previous_headers + [header], toplevel=False):
                    yield o
        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break