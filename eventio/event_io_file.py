import struct
from .object_header import make_ObjectHeader
from io import BytesIO

__all__ = ['object_headers', 'yield_objects']
        
def read_all_object_headers(f, toplevel=True):
    '''f is something like io.BufferedIOBase'''
    object_headers = []
    while True:
        try:
            header = make_ObjectHeader(f, toplevel)
            payload = f.read(header.length)
            if not header.only_sub_objects:
                object_headers.append(header)
            else:
                sub_object_headers = read_all_object_headers(BytesIO(payload), toplevel=False)
                object_headers.append((header, sub_object_headers))

        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break
    return object_headers


def object_headers(path):
    with open(path, 'rb') as f:
        return read_all_object_headers(f)

def yield_all_objects(f, previous_headers=None, toplevel=True):
    if previous_headers is None:
        previous_headers = []
    while True:
        try:
            header = make_ObjectHeader(f, toplevel)
            payload = f.read(header.length)
            if not header.only_sub_objects:
                yield previous_headers + [header], payload
            else:
                for o in yield_all_objects(BytesIO(payload), previous_headers + [header], toplevel=False):
                    yield o
        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break

def yield_objects(path):
    with open(path, 'rb') as f:
        for o in yield_all_objects(f):
            yield o
