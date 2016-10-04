import struct
from .object_header import ObjectHeader
from io import BytesIO

class EventIoObject:
    def __init__(self, payload):
        self.payload = payload

def read_all_objects(f, toplevel=True):
    '''f is something like io.BufferedIOBase'''
    objects = []
    while True:
        try:
            header = ObjectHeader(f, toplevel)
            payload = f.read(header.length)
            if not header.only_sub_objects:
                objects.append((header, EventIoObject(payload)))
            else:
                sub_objects = read_all_objects(BytesIO(payload), toplevel=False)
                objects.append((header, sub_objects))

        except ValueError:
            warnings.warn('File seems to be truncated')
            break
        except struct.error:
            break
    return objects


class EventIOFile:
    def __init__(self, path):
        toplevel = True
        with open(path, 'rb') as f:
            self.objects = read_all_objects(f, toplevel=True)

        

