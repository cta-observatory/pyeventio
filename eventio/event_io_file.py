import struct
from .object_header import ObjectHeader

class EventIoObject:
    def __init__(self, payload):
        self.payload = payload

class EventIOFile:
    def __init__(self, path):

        toplevel = True
        self.objects = []
        with open(path, 'rb') as f:
            while True:
                try:
                    header = ObjectHeader(f, toplevel)
                    self.objects.append((header, EventIoObject(f.read(header.length))))
                except ValueError:
                    warnings.warn('File seems to be truncated')
                    break
                except struct.error:
                    break

        

