from .base import EventIOFile, KNOWN_OBJECTS
from .iact import File
from . import simtel
from .histograms import Histograms

__all__ = ['EventIOFile', 'File', 'simtel']


KNOWN_OBJECTS[Histograms.eventio_type] = Histograms
